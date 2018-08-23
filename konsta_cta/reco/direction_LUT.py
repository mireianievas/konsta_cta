"""
LUT for direction reconstruction.
"""


from ctapipe.coordinates import CameraFrame, HorizonFrame
from astropy.coordinates import SkyCoord
from astropy.coordinates.angle_utilities import angular_separation

from konsta_cta.reco.lookup_base import *
from astropy import units as u
import numpy as np

from tqdm import tqdm


class LookupGenerator(LookupBase):
    """
    class to generate a look up tabel for the weights of
    the planes in the HillasReconstructor.

    The generator has to be initialized before starting
    the main analysis loop. With the method `collect_data`
    being called in the event loop the required information
    is collected. Afterwards `make_lookup` can be used, to
    generate the set of the look up tables.
    """

    def __init__(self):
        self.data = {}
        super().__init__()

    def collect_data(self, event, hillas_dict):
        """
        Collect the data from event required for building
        the look up table.

        Parameters
        ----------
        event : `DataContainer`
        hillas_dict : Dictionary
                Dict with telescope IDs as keys and`HillasParametersContainer`
                as parameters.
        dl2_list : bool
                Write a more complete a more complete dl2 list

        Returns
        -------
        data : numpy.array
        """

        for tel_id in hillas_dict.keys():
            focal_length = event.inst.subarray.tel[tel_id].optics.equivalent_focal_length
            cam_id = event.inst.subarray.tel[tel_id].camera.cam_id
            direction_az = event.mc.az.to(u.deg)
            direction_alt = event.mc.alt.to(u.deg)

            # true position in camera
            cam_coord = self.get_position_in_cam(direction_alt,
                                                 direction_az, event, tel_id)
            dca = self.calculate_dca((cam_coord.x, cam_coord.y),
                                     hillas_dict[tel_id])

            # convert dca to degrees
            conversion_factor = (180 / (np.pi * focal_length))
            dca = dca.value * conversion_factor * u.deg

            ratio = hillas_dict[tel_id].width.value / \
                hillas_dict[tel_id].length.value
            entry = [dca.value ** 2, hillas_dict[tel_id].intensity, ratio]  # one row

            try:
                self.data[cam_id] = np.append(self.data[cam_id], [entry], axis=0)
            except KeyError:
                self.data[cam_id] = np.array([entry])

    @classmethod
    def load_data_from_files(cls, files, size_max, key="/dca_list", nbins=[10,10]):
        """
        Load data from HDF5 files and convert merge the files to self.data.
        The data will be loaded from the key and has to include the columns
        dca2, intensity, width, length and cam_id.
        self.data in the end will be a dictionary with the unique cam_ids in
        the files as keys and the data stored in numpy.arrays.

        Paramters
        ---------
        files : list
            list of HDF5 files with the data stored
        key : string
            key to the data in the HDF5 file
        """

        self = cls()

        statistic = {}
        sum_lookups = {}
        bins = {}

        for i, file in tqdm(enumerate(files), total=len(files), unit="files"):

            dca_list = pd.read_hdf(file, key)
            # get ratio between width and length
            dca_list.loc[:, "ratio"] = dca_list.width / dca_list.length

            dca_list = dca_list[np.isfinite(dca_list.loc[:,
                                            dca_list.columns!="cam_id"]).all(axis=1)] # delete NaNs and infs

            self.data = {}
            # loop through all camera types
            for cam_id in np.unique(dca_list.cam_id):
                dca_camera = dca_list[dca_list.cam_id == cam_id]

                entries = np.array(dca_camera.loc[:, ("dca2", "intensity", "ratio")])

                try:
                    self.data[cam_id] = np.append(self.data[cam_id], entries, axis=0)
                except KeyError:
                    self.data[cam_id] = entries

            self.make_lookup(size_max, bins=nbins)

            LUT = self.lookup

            for cam in LUT.keys():
                cam = str(cam)
                dimensions = np.shape(LUT[cam])[0] - 2

                # merge all LUTs
                try:
                    statistic[cam] += LUT[cam][0]
                    sum_lookups[cam] = self.sum_nan_arrays(sum_lookups[cam],
                                                           LUT[cam][0] * LUT[cam][-1])

                except KeyError:
                    statistic[cam] = LUT[cam][0]
                    sum_lookups[cam] = LUT[cam][0] * LUT[cam][-1]

                    bins[cam] = []
                    for i in range(dimensions):
                        bins[cam] += [LUT[cam][i + 1]]

        self = cls()
        for cam in statistic.keys():
            sum_lookups[cam] = sum_lookups[cam] / statistic[cam]

            self.lookup[cam] = np.array(
                [statistic[cam]] + bins[cam] + [sum_lookups[cam]])

        return self

    @staticmethod
    def get_position_in_cam(dir_alt, dir_az, event, tel_id):
        """
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
        """

        # pointing direction of telescope
        pointing_az = event.mc.tel[tel_id].azimuth_raw * u.rad
        pointing_alt = event.mc.tel[tel_id].altitude_raw * u.rad

        pointing = SkyCoord(
            alt=pointing_alt,
            az=pointing_az,
            frame='altaz')

        focal_length = event.inst.subarray.tel[tel_id].\
            optics.equivalent_focal_length

        cf = CameraFrame(
            focal_length=focal_length,
            array_direction=pointing,
            pointing_direction=pointing)

        # direction of event
        direction = HorizonFrame(alt=dir_alt, az=dir_az)
        cam_coord = direction.transform_to(cf)

        return cam_coord

    def calculate_dca(self, point, params):
        """
        calculate distance of closest approach between
        Hillas major semi-axis and a point in the camera.

        Parameters
        ----------
        point : tuple or list
                position x and y in camera
        params : `HillasParametersContainer`
        """
        m = np.tan(params.psi.to(u.deg)) # slope of line

        B = 1 # might be fixed to arbitrary value
        A = - m * B
        C = (m * params.x - params.y) * B

        dca = np.abs(A * point[0] + B * point[1] + C) / np.sqrt(A**2 + B**2)

        return dca

    def make_lookup(self, size_max, bins=[10, 10]):
        """
        Create lookup tables for the weighting of the telescopes

        Parameters
        ----------
        size_max : dictionary
                Dict with the maximum size values for the LUT
                for each telescope type
        bins : tuple or list
                Number of bins in size and width to length ratio

        Returns
        -------
        lookup: dictionary
                For each camera ID one tuple containing a numpy
                array with the histogram and the look up table.
        """
        lookup = {}
        for cam in self.data.keys():
            # make sure that entries are valid
            self.data[cam] = self.data[cam][
                np.isfinite(self.data[cam]).all(axis=1)]

            xbins = np.logspace(1, np.log10(size_max[cam]), bins[0] + 1)
            ybins = np.linspace(0, 1, bins[1] + 1)

            hist = np.histogram2d(self.data[cam][:, 1], self.data[
                                  cam][:, 2], [xbins, ybins])

            # code snippet from numpy.histogramdd to calculate the bin number
            # each sample falls into. This is used in histogram2d above as well
            # but as those required numbers are not written out it is
            # reacalculated right here.
            sample = np.array([self.data[cam][:, 1], self.data[cam][:, 2]]).T
            D = sample.shape[1]

            edges = np.array([xbins, ybins])
            dedges = D * [None]

            Ncount = {}
            for i in np.arange(D):
                Ncount[i] = np.digitize(sample[:, i], edges[i])

            for i in np.arange(D):
                dedges[i] = np.diff(edges[i])
                # Rounding precision
                mindiff = dedges[i].min()

                if not np.isinf(mindiff):
                    decimal = int(-np.log10(mindiff)) + 6
                    # Find which points are on the rightmost edge.
                    not_smaller_than_edge = (sample[:, i] >= edges[i][-1])
                    on_edge = (np.around(sample[:, i], decimal) ==
                               np.around(edges[i][-1], decimal))

                    # Shift these points one bin to the left.
                    Ncount[i][np.nonzero(on_edge & not_smaller_than_edge)[0]] -= 1

            sum_dca2 = np.zeros([len(xbins), len(ybins)])
            for i, dca2 in enumerate(self.data[cam][:, 0]):
                sum_dca2[Ncount[0][i] - 1, Ncount[1][i] - 1] += dca2
            dca2_means = sum_dca2[:-1,:-1] / hist[0]

            # add to the histogram
            self.lookup[cam] = np.array(hist + (np.reshape(dca2_means, bins),))

    def get_weight_from_LUT(self, params, cam_id, min_stat=5, ratio_cut=1.):
        """
        Get the weight from a LUT.

        Parameters
        ----------
        params : `HillasParametersContainer`
        cam_id : string
            table to look value up
        min_stat : integer
            minimum number of entries required in each bin
        ratio_cut : integer or float
            maximum value of ratio width to length to considere
            in analysis

        Returns
        -------
        weight : float
            1 / mean squared dca

        Raises
        ------
        ValueError
            if the statistic in the bin is below required value
            `min_stat` or if the ratio of width to length is above
            the cut
        """
        ratio = params.width / params.length
        if ratio > ratio_cut:
            # apply cut on the width to length ratio
            raise LookupFailedError("Ratio width to length above allowed"
                             " value of {}".format(ratio_cut))

        statistic, mean_dca2 = self.look_up_value([params.intensity, ratio],
                                                cam_id)
        if statistic < min_stat:
            raise LookupFailedError("Not enough statistics in bin.")

        weight = 1 / mean_dca2

        return weight

