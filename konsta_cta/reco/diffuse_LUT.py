import pandas as pd
import numpy as np
import pickle
from konsta_cta.reco.lookup_base import LookupFailedError
from konsta_cta.reco.direction_LUT import LookupGenerator
from tqdm import tqdm


class DiffuseLUT(LookupGenerator):

    def __init__(self):
        super().__init__()
        self.difflookup = {}

    @classmethod
    def look_up_offbins(cls, files, size_max, key="/dca_list", nbins=[10,10], off_bins=None):
        """

        Parameters
        ----------
        files : list
            list with the files to use for creating the LUTs
        size_max : integer or float
            maximum size values for the LUTs of each camera
        key : string
            path to read from in the HDF files
        nbins : list or tuple
            number of bins in size and width to length ratio
        off_bins : list
            2 dimensional list containing the start and end points for each
            off angle bins in each line. For each line, one entry in
            self.lookup is created
        """
        statistic = {}
        sum_lookups = {}
        bins = {}
        if off_bins is None:
            off_bins = [0, np.inf]

        for nbin, off_bin in enumerate(off_bins):
            statistic[nbin] = {}
            sum_lookups[nbin] = {}
            bins[nbin] = {}

        for i, file in tqdm(enumerate(files), total=len(files), unit="files"):
            dca_list = pd.read_hdf(file, key)
            # get ratio between width and length
            dca_list.loc[:, "ratio"] = dca_list.width / dca_list.length

            dca_list = dca_list[np.isfinite(dca_list.loc[:,
                                            dca_list.columns!="cam_id"]).all(axis=1)] # delete NaNs and infs


            for nbin, off_bin in enumerate(off_bins):

                dca_list_bin = dca_list.loc[(dca_list.offangle >= off_bin[0]) &
                                            (dca_list.offangle <= off_bin[1])]

                # reset the dicts at each iteration so that make_lookup
                # does not take data from previous iterations if no new
                # data for a specific camera was given in that bin.
                self = cls()

                # loop through all camera types
                for cam_id in np.unique(dca_list_bin.cam_id):
                    dca_camera = dca_list_bin[dca_list_bin.cam_id == cam_id]
                    entries = np.array(dca_camera.loc[:, ("dca2", "intensity", "ratio")])

                    try:
                        self.data[cam_id] = np.append(self.data[cam_id], entries, axis=0)
                    except KeyError:
                        self.data[cam_id] = entries

                self.make_lookup(size_max, bins=nbins)
                LUT = self.lookup
                for cam_id in LUT.keys():
                    dimensions = np.shape(LUT[cam_id])[0] - 2

                    # merge all LUTs
                    try:
                        statistic[nbin][cam_id] += LUT[cam_id][0]
                        sum_lookups[nbin][cam_id] = self.sum_nan_arrays(sum_lookups[nbin][cam_id],
                                                               LUT[cam_id][0] * LUT[cam_id][-1])

                    except KeyError:
                        statistic[nbin][cam_id] = LUT[cam_id][0]
                        sum_lookups[nbin][cam_id] = LUT[cam_id][0] * LUT[cam_id][-1]

                        bins[nbin][cam_id] = []
                        for ii in range(dimensions):
                            bins[nbin][cam_id] += [LUT[cam_id][ii + 1]]

        self = cls()
        self.difflookup["bins"] = off_bins
        for nbin, off_bin in enumerate(off_bins):
            self.difflookup[nbin] = {}
            for cam_id in statistic[nbin].keys():
                sum_lookups[nbin][cam_id] = sum_lookups[nbin][cam_id] / statistic[nbin][cam_id]

                self.difflookup[nbin][cam_id] = np.array(
                    [statistic[nbin][cam_id]] + bins[nbin][cam_id] + [sum_lookups[nbin][cam_id]])

        return self

    def save_pickle(self, path):
        """
        Save LUT to pickle file.

        Parameters
        ----------
        path : string
        	file to store the LUT self.lookup into
        """
        with open(path, "wb") as file:
            pickle.dump(self.difflookup, file)

    @classmethod
    def load_pickle(cls, path):
        """
        Read look up table which was stored in a pickle file

        Parameters
        ----------
        path : string
            path to the `json` file which stores the LUT

        Returns
        -------
        self : DiffuseLUT
            in derived classes, it will return a instance of
            that class for further usage
        """
        self = cls()

        with open(path, "rb") as file:
            self.difflookup = pickle.load(file)

        return self

    def get_weight_from_diffuse_LUT(self, params, offangle, cam_id, min_stat=5, ratio_cut=1.):
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

        # select the LUT according to the offangle bin
        offbin = int(np.sum(np.array(self.difflookup["bins"]) < offangle) / 2)
        try:
            self.lookup = self.difflookup[offbin]
        except KeyError:
            # value outside of LUT. Select from last table.
            offbin = list(self.difflookup.keys())[-1]
            self.lookup = self.difflookup[offbin]

        statistic, mean_dca2 = self.look_up_value([params.intensity, ratio],
                                                cam_id)

        if statistic < min_stat:
            raise LookupFailedError("Not enough statistics in bin.")

        weight = 1 / mean_dca2

        return weight
