from astropy import units as u
import numpy as np
import pickle


class LookupFailedError(Exception):
    '''Error when the the look up from table failed'''
    pass


def get_position_in_cam(dir_alt, dir_az, event, tel_id):
    '''
    transform position in HorizonFrame to CameraFrame

    Parameters
    ----------
    dir_alt : direction altitude
    dir_az : direction azimuth
    event : event data container
    tel_id : telescope ID

    Returns
    -------
    cam_coord : position in camera of telescope tel_id
    '''

    from ctapipe.coordinates import CameraFrame, HorizonFrame
    from astropy.coordinates import SkyCoord

    # pointing direction of telescope
    pointing_az = event.mc.tel[tel_id].azimuth_raw * u.rad  # add units
    pointing_alt = event.mc.tel[tel_id].altitude_raw * u.rad

    # pointing of array
    pointing = SkyCoord(
        alt=pointing_alt,
        az=pointing_az,
        frame='altaz')

    # focal length of telescope
    focal_length = event.inst.subarray.tel[tel_id].\
        optics.equivalent_focal_length

    cf = CameraFrame(
        focal_length=focal_length,
        array_direction=pointing,
        pointing_direction=pointing)

    # direction of event
    direction = HorizonFrame(
        alt=dir_alt,
        az=dir_az)

    cam_coord = direction.transform_to(cf)

    return cam_coord


def calculate_dca(point, params):
    '''
    calculate distance of closest approach between
    Hillas major semi-axis and a point in the camera.

    Parameters
    ----------
    point : tuple or list
	    position x and y in camera
    params : `HillasParametersContainer`
    '''
    A = np.tan(params.psi.to(u.deg))
    B = 1
    C = -(- A * params.x + params.y)

    dca = np.abs(A * point[0] + B * point[1] + C) / np.sqrt(A**2 + B**2)

    return dca


def make_lookup(data, size_max, bins=[10, 10]):
    '''
    Create lookup tables for the weighting of the telescopes

    Parameters
    ----------
    data : dictinoary
            Dict with camera IDs as keys and pandas
            DataFrames as values. Those DataFrames has to
            contain the columns width, length, size and dca
    size_max : dictionary
            Dicts with the maximum size values for the LUT
            for each telescopes
    bins : tuple or list
            Number of bins in size and width to length ratio

    Returns
    -------
    lookup: dictionary
            For each camera ID one tuple containing a tuple
            with the histogram as well as the look up table.	
    '''
    lookup = {}
    for cam in data.keys():
        # prepare data frame
        df = data[cam]
        df["ratio_lw"] = df.width / df.length
        # make sure that entries are valid
        df = df[np.isfinite(df)]
        df = df.dropna()

        xbinslog = np.linspace(
            np.log10(1), np.log10(size_max[cam]), bins[0] + 1)
        xbins = np.power(10, xbinslog)
        ybins = np.linspace(0, 1, bins[1] + 1)

        hist = np.histogram2d(df.intensity, df.ratio_lw, (xbins, ybins))

        dca2_means = []
        for i in range(len(xbins) - 1):
            for k in range(len(ybins) - 1):
                subset = df.loc[(df.intensity >= hist[1][i]) &
                                (df.intensity <= hist[1][i + 1]) &
                                (df.ratio_lw >= hist[2][k]) &
                                (df.ratio_lw <= hist[2][k + 1])]

                dca2_means.append(subset.dca2.mean())

        # add the mean dca values to the histogram output
        lookup[cam] = hist + (np.reshape(dca2_means, bins),)

    return lookup


def sum_nan_arrays(arr_a, arr_b):
    '''
    Sum two numpy arrays and threat np.nans as zero
    if the the other array's entry is none nan at the
    same position. If both values are nans leave it as
    it was.

    Parameters
    ----------
    arr_a : nunmpy.array
    arr_b : nunmpy.array

    Returns
    -------
    summed_array : sum of the input arrays
    '''

    mask_a = np.isnan(arr_a)
    mask_b = np.isnan(arr_b)

    # mask with positions where to keep the values
    m_keep_a = ~mask_a & mask_b
    m_keep_b = mask_a & ~mask_b

    sumed_array = arr_a + arr_b
    sumed_array[m_keep_a] = arr_a[m_keep_a]
    sumed_array[m_keep_b] = arr_b[m_keep_b]

    return sumed_array


def combine_LUTs(files):
    '''
    Combine the resulting LUTs of several files
    to one final LUT.

    Parameters
    ----------
    files :  list
	    list with paths to files of LUTs each file
        containes tuple with number of events, bin
        edges in size, bin edges in w/l ratio and
        the mean dca values.

    Returns
    -------
    LUT : Dictionary
            Dictionary with camera IDs as keys and tuples
            of combined mean DCA values, and histogram.
    '''
    statistic = {}
    combined_LUT = {}
    bins_size = {}
    bins_ratio = {}
    LUT = {}

    for file in files:
        with open(file, "rb") as f:
            LUT = pickle.load(f)

        for cam in LUT.keys():
            # merge all LUTs
            try:
                statistic[cam] += LUT[cam][0]
                combined_LUT[cam] = sum_nan_arrays(
                    combined_LUT[cam], LUT[cam][0] * LUT[cam][3])
            except KeyError:
                statistic[cam] = LUT[cam][0]
                combined_LUT[cam] = LUT[cam][0] * LUT[cam][3]
                bins_size[cam] = LUT[cam][1]
                bins_ratio[cam] = LUT[cam][2]

    for cam in LUT.keys():
        combined_LUT[cam] = combined_LUT[cam] / statistic[cam]

        LUT[cam] = (statistic[cam], bins_size[cam],
                    bins_ratio[cam], combined_LUT[cam])

    return LUT


def get_weight_from_LUT(params, LUT, min_stat=5, ratio_cut=1.):
    '''
    Get the weight from a LUT.

    Parameters
    ----------
    params : `HillasParametersContainer`
    LUT : dict containing LUT, statistic and bin endges
    min_stat : minimum number of entries required in bin

    Returns
    -------
    weight : 1 / mean_dca read from LUT
    '''
    ratio = params.width / params.length
    if ratio > ratio_cut:
        # apply cut on the width to length ratio
        raise ValueError("Ratio width to length above allowed"
                         " value of {}".format(ratio_cut))
    try:
        bin_ratio = np.arange(len(LUT[2]))[ratio > LUT[2]][-1]
        bin_size = np.arange(len(LUT[1]))[params.intensity > LUT[1]][-1]

        statistic = int(LUT[0][bin_size, bin_ratio])
        mean_dca2 = LUT[3][bin_size, bin_ratio]

    except IndexError:
        raise LookupFailedError("Values outside of LUT.")

    if statistic < min_stat:
        raise LookupFailedError("Not enough statistics in bin.")

    weight = 1 / mean_dca2

    return weight
