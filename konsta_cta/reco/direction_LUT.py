"""
LUT for direction reconstruction.
"""


from ctapipe.coordinates import CameraFrame, HorizonFrame
from astropy.coordinates import SkyCoord

from konsta_cta.reco.lookup_base import *
from astropy import units as u
import numpy as np


class LookupGenerator(LookupBase):
    '''
    class to generate a look up tabel for the weights of
    the planes in the HillasReconstructor.

    The generator has to be initialized before starting
    the main analysis loop. With the method `collect_data`
    being called in the event loop the required information
    is collected. Afterwards `make_lookup` can be used, to
    generate the set of the look up tables.
    '''

    def __init__(self):
        self.data = {}
        super().__init__()

    def collect_data(self, event, hillas_dict):
        '''
        Collect the data from event required for building
        the look up table.

        Parameters
        ----------
        event : `DataContainer`
        hillas_dict : Dictionary
                Dict with telescope IDs as keys and`HillasParametersContainer`
                as parameters.

        Returns
        -------
        data : numpy.array
        '''

        for tel_id in hillas_dict.keys():

            cam_id = event.inst.subarray.tel[tel_id].camera.cam_id
            direction_az = event.mc.az.to(u.deg)
            direction_alt = event.mc.alt.to(u.deg)

            # true position in camera
            cam_coord = self.get_position_in_cam(direction_alt,
                                                 direction_az, event, tel_id)
            dca = self.calculate_dca((cam_coord.x, cam_coord.y),
                                     hillas_dict[tel_id])

            ratio = hillas_dict[tel_id].width.value / \
                hillas_dict[tel_id].length.value
            entry = [dca.value**2,
                     hillas_dict[tel_id].intensity, ratio]  # one row

            try:
                self.data[cam_id] = np.append(self.data[cam_id], [entry], axis=0)
            except KeyError:
                self.data[cam_id] = np.array([entry])

    def get_position_in_cam(self, dir_alt, dir_az, event, tel_id):
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

    def make_lookup(self, size_max, bins=[10, 10]):
        '''
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
        '''
        lookup = {}
        for cam in self.data.keys():
            # make sure that entries are valid
            self.data[cam] = self.data[cam][
                np.isfinite(self.data[cam]).all(axis=1)]

            xbins = np.logspace(1, np.log10(size_max[cam]), bins[0] + 1)
            ybins = np.linspace(0, 1, bins[1] + 1)

            hist = np.histogram2d(self.data[cam][:, 1], self.data[
                                  cam][:, 2], [xbins, ybins])

            dca2_means = []
            for i in range(len(xbins) - 1):
                for k in range(len(ybins) - 1):
                    mask = ((self.data[cam][:, 1] >= hist[1][i]) &
                            (self.data[cam][:, 1] <= hist[1][i + 1]) &
                            (self.data[cam][:, 2] >= hist[2][k]) &
                            (self.data[cam][:, 2] <= hist[2][k + 1]))

                    subset = self.data[cam][mask, :]

                    # mean squared dca values in bin
                    dca2_means.append(np.mean(subset[:, 0]))

            # add to the histogram
            self.lookup[cam] = np.array(hist + (np.reshape(dca2_means, bins),))

        #return self.lookup

    def get_weight_from_LUT(self, params, cam_id, min_stat=5, ratio_cut=1.):
        '''
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
        '''
        ratio = params.width / params.length
        if ratio > ratio_cut:
            # apply cut on the width to length ratio
            raise ValueError("Ratio width to length above allowed"
                             " value of {}".format(ratio_cut))

        statistic, mean_dca2 = self.look_up_value([params.intensity, ratio],
                                                cam_id)
        if statistic < min_stat:
            raise ValueError("Not enough statistics in bin.")

        weight = 1 / mean_dca2

        return weight

