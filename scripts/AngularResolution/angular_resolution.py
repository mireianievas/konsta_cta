import glob
import os
import argparse

import pandas as pd
import numpy as np

from tqdm import tqdm

import plotting
import datetime

def multiplicity_cut(data, energies, multiplicity):
    """
    Apply the multiplicity cuts to a pandas.DataFrame. Expects the
    column names MC_Energy and multiplicity.

    Parameters
    ----------
    energies : list
        Energy bins
    multiplicity : list
        list of multiplicity cuts. len(multiplicity) should be (at maximum)
        len(energies) - 1.

    Returns
    -------
    data : pandas.DataFrame
        dataframe with rows not passing the cuts removed
    """

    for i in range(len(multiplicity)):
        ebin = (data.loc[:, "MC_Energy"] > energies[i]) & \
               (data.loc[:, "MC_Energy"] < energies[i + 1])
        drop = data[ebin & (data.loc[:, "multiplicity"] <\
                            mulitplicitycuts[1][i])].index
        data = data.drop(drop)

    return data


def load_data(files, multiplicitycuts=None, maxfiles=None):
    """
    files : list
        list with paths to hdf5 files to read the data to
    data : pandas.DataFrame
        Appended data loaded from files
    """

    files = files[:maxfiles]
    for file in files:
        try:
            datafile = pd.read_hdf(file, key="direction_reconstriction").iloc[:, [0, 4, 5, 6]]
            #if multiplicitycuts is not None:
            #    datafile = multiplicity_cut(datafile, multiplicitycuts[0], multiplicitycuts[1])
        except (HDF5ExtError, OSError):
            print("Not able to read {}".format(file))
            continue
        try:
            data = pd.concat([data, datafile])
        except NameError:
            data = datafile

    print("Total number of events: ", len(data))
    data = data.reset_index(drop=True) # unique indices required before drop
    if multiplicitycuts is not None:
        data = multiplicity_cut(data, multiplicitycuts[0], multiplicitycuts[1])
    print("After multiplicity cut: ", len(data))

    return data

# def load_data(files, maxfiles=None):
#     """
#     files : list
#         list with paths to hdf5 files to read the data to
#     data : pandas.DataFrame
#         Appended data loaded from files
#     """
#     files = files[:maxfiles]
#     for file in tqdm(files, total=len(files)):
#         try:
#             datafile = pd.read_hdf(file, key="direction_reconstriction").iloc[:, [1, 6, 7]]
#         except (OSError):
#             print("Not able to read {}".format(file))
#             continue
#
#         try:
#             data = pd.concat([data, datafile])
#         except NameError:
#             data = datafile
# 
#     return data

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir' , default="/lustre/fs19/group/cta/users/kpfrang/software/ctapipe_output/")
    parser.add_argument('--directories', nargs='*', required=True)
    parser.add_argument('--names', nargs='*', required=True)
    # parser.add_argument('--type', nargs='*', required=True)
    parser.add_argument('--odir', default="./AngularResolutionPlots")
    parser.add_argument('--outname', default="None")
    parser.add_argument('--offsets', nargs="*", default=[-1, 100], type=float)
    parser.add_argument('--maxfiles', type=int, default=-1)

    args = parser.parse_args()
    if args.maxfiles < 0:
        maxfiles = None
    else:
        maxfiles = args.maxfiles

    time_start = datetime.datetime.now()

    if args.offsets == [-1, 100]:
        odir = "{}/point".format(args.odir)
    else:
        for offset in args.offsets:
            try:
                fname += "_{}".format(offset)
            except NameError:
                fname = str(offset)

            odir = "{}/{}".format(args.odir, fname)

    directory = os.getcwd()
    if odir[0] != "/":
        odir = directory + "/" + odir

    if not (os.path.isdir(odir)):
        os.makedirs(odir)

    # multiplicity cuts
    logEcut = np.arange(-1.9, 2.4, 0.2)
    Ecut = np.power(10, logEcut)
    multicut = [3, 3, 3, 3, 4, 3, 3, 4, 6, 6, 5, 4, 6, 6, 6, 4, 4, 3, 2, 2, 2]
    mulitplicitycuts = [Ecut, multicut]

    data_dict = {}
    for directory, name in zip(args.directories, args.names):
        datadir = os.path.abspath("{}/{}".format(args.basedir, directory))
        print("Loading files from directory '{}'.".format(datadir))
        files = glob.glob("{}/output*.h5".format(datadir))
        data_dict[name] = load_data(files, multiplicitycuts=mulitplicitycuts, maxfiles=maxfiles)

    # building a output name
    base_dirs = [directory.split("/")[0] for directory in args.directories]
    base_dirs = np.unique(base_dirs)
    for base in base_dirs:
        try:
            plotname += "_{}".format(base)
        except NameError:
            plotname = "_{}".format(base)

        for directory, name in zip(args.directories, args.names):
            if base in directory:
                plotname += "_{}".format(name)

    if args.offsets != [-1, 100]:
        plotname += "_offsets"
        for offset in args.offsets:
            plotname += "_{}".format(offset)

    # # plot everybin in same plot
    if args.offsets == [-1, 100]:
        plotting.plot_all(data_dict, args.offsets, args.names, odir, plotname, args.outname)

    ################################
    # one plot for each name
    plotting.plot_per_name(data_dict, args.offsets, args.names, odir, args.outname)

    plotting.plot_per_offbin(data_dict, args.offsets, args.names, odir, args.outname)

    #if (len(args.names) >= 2) & ("default" in args.names):
        ################################
        # improvement over default
    #    plot_improvement(data_dict, args.offsets, args.names, odir, plotname, args.outname)

    if (len(args.names) > 1):
        plotting.plot_improvement_methods(data_dict, args.offsets, args.names, odir, args.outname)

    time_stop = datetime.datetime.now()
    print("------------- Finished -------------")
    print("Time required: {}".format(time_stop - time_start))