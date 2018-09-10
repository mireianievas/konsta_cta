import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from konsta_cta.reco import *

def make_lookup_from_list(dca_list, cameras=None, offangle_bins=None,
                          size_max=None, bins=[20,20]):
    """
    create a lookup table from the dca feature list.

    Parameters
    ----------
    dca_list : pandas.DataFrame
        list of dca features written out by analysi_file_write
        in write_list_dca mode
    cameras : dictionary
        lookup to translate id to camera names
    offangle_bins : list or None
        list defining the bins in offangle to create one table
        each. If None, all events are taken to create one table
    size_max : dictionary
        dictionary with the camera names as keys and the maximum
        value of size for each of the cameras
    bins : list or tuple
        number of bins in size and w/l ratio
    minstat : int or float
        minimum statistic in each bin to consider a bin valid.
        If the number of entries in this bin is below that number,
        a numpy.NaN is taken for this bin.
    """
    if cameras is None:
        cameras = {0: "LSTCam",
                   1: "FlashCam",
                   2: "NectarCam",
                   3: "CHEC",
                   4: "DigiCam",
                   5: "ASTRICam"}
    if size_max is None:
        size_max = {
            "NectarCam": 3000000,
            "FlashCam": 3000000,
            "LSTCam": 3000000,
            "ASTRICam": 3000000,
            "DigiCam": 800000,
            "CHEC": 800000
        }

    dca_list = dca_list.dropna()

    dca_list.is_copy = False
    dca_list.loc[:, ("ratio")] = dca_list.width / dca_list.length

    LUTs = {"bins": offangle_bins}

    for bin, offangle_bin in enumerate(offangle_bins[:-1]):
        LUTs[bin] = {}
        data_bin = dca_list[(dca_list.offangle > offangle_bins[bin]) &
                            (dca_list.offangle < offangle_bins[bin + 1])]

        for camera in cameras:

            xbins = np.logspace(1, np.log10(size_max[cameras[camera]]), bins[0]+1 )
            ybins = np.linspace(0, 1, bins[1] + 1)

            data_camera = data_bin[dca_list.cam_id == camera]

            hist = np.histogram2d(data_camera.intensity,
                                  data_camera.ratio,
                                  [xbins, ybins])

            # code snippet from numpy.histogramdd to calculate the bin number
            # each sample falls into. This is used in histogram2d above as well
            # but as those required numbers are not written out it is
            # reacalculated right here which still results in a 15 time faster.

            sample = np.array([data_camera.intensity, data_camera.ratio]).T
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
            for i, dca2 in enumerate(data_camera.dca2):
                sum_dca2[Ncount[0][i] - 1, Ncount[1][i] - 1] += dca2

            dca2_means = sum_dca2[:-1,:-1] / hist[0]

            LUTs[bin][cameras[camera]] = np.array(hist + (np.reshape(dca2_means, bins),))

    return LUTs

def merge_verbose_LUTs(files, minstat=0):
    '''
    Merge several LUT from different files to one

    :param files: list of files with verbose diffuse LUTs
    :param minstat: minimum number of events requred per bin
    :return mergedLUT: merged look up tables

    '''
    with open(files[0], "rb") as f:
        LUTs = pickle.load(f)
    offbins = LUTs["bins"]
    mergedLUT = {"bins": offbins}

    for offbin in range(len(offbins) - 1):
        statistic = {}
        sum_lookups = {}
        bins = {}
        LUT = {}
        for file in files:
            with open(file, "rb") as f:
                LUTs = pickle.load(f)

            for cam in LUTs[offbin].keys():
                if cam != "bins":
                    try:
                        statistic[cam] += LUTs[offbin][cam][0]
                        sum_lookups[cam] = LookupGenerator.sum_nan_arrays(sum_lookups[cam],
                                                                          LUTs[offbin][cam][0] * LUTs[offbin][cam][-1])

                    except KeyError:
                        statistic[cam] = LUTs[offbin][cam][0]
                        sum_lookups[cam] = LUTs[offbin][cam][0] * LUTs[offbin][cam][-1]

                        bins[cam] = []
                        for i in range(2):
                            bins[cam] += [LUTs[offbin][cam][i + 1]]

        for cam in statistic.keys():
            sum_lookups[cam] = sum_lookups[cam] / statistic[cam]

            if minstat > 0:
                mask = statistic[cam] < minstat
                sum_lookups[cam][mask] = np.nan

            LUT[cam] = np.array(
                [statistic[cam]] + bins[cam] + [sum_lookups[cam]])

        mergedLUT[offbin] = LUT

    return mergedLUT

def get_vrange(LUTs, min_stat=0):
    '''
    Get the maximum and minimum vrange for each camera

    Parameters
    ----------
    LUTs: dictionary

    Returns
    -------
    max_val: dict
        maximum v-values for each camera
    min_val: dict
        minimum v-values for each camera
    '''

    for offbin in LUTs:
        if type(offbin) == int:
            for cam in LUTs[offbin]:

                mask = LUTs[offbin][cam][0] > min_stat

                LUT = LUTs[offbin][cam][-1][mask]

                maximum = np.max(LUT[~np.isnan(LUT)])
                minimum = np.min(LUT[~np.isnan(LUT)])
                try:
                    if maximum > max_val[cam]:
                        max_val[cam] = maximum
                    if minimum < min_val[cam]:
                        min_val[cam] = minimum
                except NameError:
                    max_val = {cam: maximum}
                    min_val = {cam: minimum}
                except KeyError:
                    max_val[cam] = maximum
                    min_val[cam] = minimum
    return max_val, min_val


def plot_verbose(LUTs, figsize=[15, 15], cameras=None, max_val=None, min_val=None,
                 min_stat=0, colorbar=True):
    '''
    Plot the LUTs in each bin

    Parameters
    ----------
    LUTs: dictionary

    Returns
    -------
    max_val: dict
        maximum v-values for each camera
    min_val: dict
        minimum v-values for each camera
    '''
    if cameras == None:
        cameras = ['LSTCam', 'FlashCam', 'NectarCam', 'CHEC', 'DigiCam', 'ASTRICam']
    if not max_val is None:
        max_val = max(max_val.values())
    if not min_val is None:
        min_val = min(min_val.values())

    fig, axarr = plt.subplots(len(cameras), len(LUTs["bins"]), figsize=figsize)

    for k, cam in enumerate(cameras):

        nbins = np.sort(list(LUTs.keys()))
        for i, nbin in enumerate(nbins):
            try:
                nbin = int(nbin)
            except ValueError:
                continue

            axarr[k, i].set_xscale("log")
            try:
                LUT = LUTs[nbin][cam][-1]
                # cut on number of events in bin
                mask = LUTs[nbin][cam][0] < min_stat
                LUT[mask] = np.NaN

                LUT = LUT.T

                xbins, ybins = (LUTs[nbin][cam][1], LUTs[nbin][cam][2])
                # print(len(xbins))
                val = axarr[k, i].pcolormesh(xbins, ybins, LUT, alpha=1.,
                                             cmap="inferno", norm=LogNorm(),
                                             vmin=min_val, vmax=max_val)
            except KeyError:
                pass

            # remove ticks
            if k != (len(cameras) - 1):
                axarr[k, i].set_xlim([min(xbins), max(xbins)])
                axarr[k, i].set_xticks([])
            else:
                axarr[k, i].set_xlabel("size / pe", fontsize=15)
                axarr[k, i].set_xlim([min(xbins), max(xbins)])

            if i != 0:
                axarr[k, i].set_yticks([])
            else:
                axarr[k, i].set_ylabel("{}\nwidth / length".format(cam), fontsize=15)
                axarr[k, i].set_ylim([min(ybins), max(ybins)])

            # add labels to columns and rows
            if i == len(LUTs["bins"]) - 1:
                # ax2 = axarr[k, i].twinx()
                # lab = ax2.set_ylabel(cam, fontsize=20, labelpad=90)
                # ax2.set_yticks([])

                if colorbar:
                    cbar = plt.colorbar(val, ax=axarr[k, i], norm=LogNorm())
                    cbar.set_label('<DCA$^2$> (deg$^2$)')

            if k == 0:
                if type(LUTs["bins"][nbin]) == list:
                    axarr[k, i].set_title("{:.1f}$^\circ$ - {:.1f}$^\circ$".format(LUTs["bins"][nbin][0],
                                                                       LUTs["bins"][nbin][1]), fontsize=20)
                elif type(LUTs["bins"][nbin]) == str:
                    axarr[k, i].set_title(LUTs["bins"][nbin], fontsize=20)

        plt.tight_layout()
        plt.subplots_adjust(wspace=0.05, hspace=0.05)


