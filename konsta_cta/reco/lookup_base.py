import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import json
import pandas as pd


class LookupFailedError(Exception):
    pass


class LookupBase:
    """
    Base class for handeling look up tables. The lookup tables
    are expected to be a tuple with arrays for statistics which
    contains the number of entries for each bin, one array for
    each dimension containing the edges of the bins and one
    array with the look up values.
    """

    def __init__(self):
        self.lookup = {}

    def save(self, path):
        """
        Save a lookuptable to a file using json

        Parameters
        ----------
        path : string
        	file to store the LUT self.lookup into
        """
        dict_to_save = {}
        for key in self.lookup.keys():
            dict_to_save[key] = [l.tolist() for l in self.lookup[key]]

        dump = json.dumps(dict_to_save)
        with open(path, "w") as f:
            f.write(dump)

    @classmethod
    def load(cls, path):
        """
        Read look up table and converte arrays to numpy.arrays

        Parameters
        ----------
        path : string
            path to the `json` file which stores the LUT

        Returns
        -------
        self : LookupBase
            in derived classes, it will return a instance of
            that class for further usage
        """
        self = cls()

        with open(path) as f:
            lookup = json.load(f)

        for key in lookup.keys():
            self.lookup[key] = np.array([np.array(l) for l in lookup[key]])

        return self

    @staticmethod
    def sum_nan_arrays(arr_a, arr_b):
        """
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
        """

        mask_a = np.isnan(arr_a)
        mask_b = np.isnan(arr_b)

        # mask with positions where to keep the values
        m_keep_a = ~mask_a & mask_b
        m_keep_b = mask_a & ~mask_b

        sumed_array = arr_a + arr_b
        sumed_array[m_keep_a] = arr_a[m_keep_a]
        sumed_array[m_keep_b] = arr_b[m_keep_b]

        return sumed_array

    @classmethod
    def combine_LUTs(cls, files):
        """
        Combine the resulting LUTs of multible files
        to one lookup table.

        Parameters
        ----------
        files :  list
            list with paths to files of LUTs each file
            containes tuple with number of events, bin
            edges in size, bin edges in w/l ratio and
            the mean dca values.

        Returns
        -------
        lookup : Dictionary
            Dictionary with camera IDs as keys and numpy
            array of combined look up table.
        """

        statistic = {}
        sum_lookups = {}
        bins = {}

        self = cls()
        for file in files:
            loaded = self.load(file)

            for cam in loaded.lookup.keys():
                dimensions = np.shape(loaded.lookup[cam])[0] - 2

                # merge all LUTs
                try:
                    statistic[cam] += loaded.lookup[cam][0]
                    sum_lookups[cam] = self.sum_nan_arrays(sum_lookups[cam],
                                                           loaded.lookup[cam][0] * loaded.lookup[cam][-1])

                except KeyError:
                    statistic[cam] = loaded.lookup[cam][0]
                    sum_lookups[cam] = loaded.lookup[
                        cam][0] * loaded.lookup[cam][-1]

                    bins[cam] = []
                    for i in range(dimensions):
                        bins[cam] += [loaded.lookup[cam][i + 1]]

                # control if binning is equal
                bins_match = True
                for i in range(dimensions):
                    bins_match = (bins_match and (
                        bins[cam][i] == loaded.lookup[cam][i + 1]).all())

                if not bins_match:
                    raise AttributeError("Binning does not match"
                                         " in file {}".format(file))

        for cam in statistic.keys():
            sum_lookups[cam] = sum_lookups[cam] / statistic[cam]

            self.lookup[cam] = np.array(
                [statistic[cam]] + bins[cam] + [sum_lookups[cam]])

        return self

    def look_up_value(self, params, cam_id):
        """
        Get the value and number of entries to a given set of
        parameters. The number of parameters passed must be
        equal to the number of of dimensions the look up table
        has.

        Parameters
        ----------
        params : tuple or list
            a list or tuple with parameters to look for
        cam_id : string
            cam_id for the key of the lookup dictionary

        Returns
        -------
        weight : float
            1 / mean squared dca

        Raises
        ------
        LookupFailedError
            if the parameters are not in range of LUT
        """

        dims = np.shape(self.lookup[cam_id])[0] - 2
        if dims != len(params):
            raise AttributeError("Lookup table with {dim} dimentsions "
                                 "takes exactly {dim} params for lookup, not "
                                 "{pars}.".format(dim=dims, pars=len(params)))
        try:
            _bin = []
            for i in range(dims):
                _bin.append(np.arange(len(self.lookup[cam_id][i + 1]))[
                    params[i] > self.lookup[cam_id][i + 1]][-1])

            statistic = int(self.lookup[cam_id][0][tuple(_bin)])
            value = self.lookup[cam_id][-1][tuple(_bin)]

        except IndexError:
            raise LookupFailedError("Values outside of LUT.")

        return statistic, value

    def display_lookup(self, xlabel="attr_1", ylabel="attr_2",
                figsize=None, xscale="log", yscale="linear",
                cmap="inferno", vmin=None, vmax=None):
        """
        plot the look up tables stored in dict self.lookup. For each
        key a new line is printed with the histogram and the lookup
        values.

        This method is only able to display a 2 dimensional LUT and
        currently won't work with lookup tables of higher dimensions.

        Parameters
        ----------
        xlabel : string
        ylabel : string
        figsize : tuple, list
        xscale : string
            scale to use for x-axis
        yscale : string
            scale to use for y-axis
        cmap : string
            python colormap
        """
        number_entries = len(self.lookup.keys())
        if figsize == None:
            figsize = [8, 3 * number_entries]

        f, axarr = plt.subplots(number_entries, 2, figsize=figsize)

        for i, (cam, lookup) in enumerate(self.lookup.items()):
            stat = lookup[0].T
            value = lookup[-1].T

            xbins, ybins = (lookup[1], lookup[2])
            stats = axarr[i, 0].pcolormesh(xbins, ybins, stat, alpha=1.,
                                           cmap=cmap, norm=LogNorm())
            dcavals = axarr[i, 1].pcolormesh(xbins, ybins, value, alpha=1.,
                                             cmap=cmap, norm=LogNorm(),
                                             vmin=vmin, vmax=vmax)

            for ax, im, label in zip([axarr[i, 0], axarr[i, 1]],
                                     [stats, dcavals],
                                     ["N$_{stat}$", "value"]):
                ax.set_xlabel(xlabel)
                ax.set_ylabel(ylabel)
                ax.set_xscale(xscale)
                ax.set_yscale(yscale)
                clb = plt.colorbar(im, ax=ax, norm=LogNorm())
                clb.ax.set_title(label)
                ax.set_title(cam)

        plt.tight_layout()
