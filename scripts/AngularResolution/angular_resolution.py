import glob
import os
import argparse

import pandas as pd
import numpy as np
from uncertainties import unumpy as un
from tqdm import tqdm

import matplotlib.pyplot as plt
from matplotlib import rcParams


def calc_angular_resolution(off_angle, trueE, q=0.68, erange=[0.01, 100], bins=10):
    '''
    off_angle - pd.Series
    true_e - pd.Series
    quantile - float
    erange - list, upper an lower edge in TeV
    ebins - int, number of bins
    '''

    ebins_log = np.linspace(np.log10(erange[0]), np.log10(erange[1]), bins+1)
    ebins = np.power(10, ebins_log)

    quantiles = np.zeros(shape=[2, bins])
    # loop over bins in energy
    for i in range(bins):

        angles_bin = off_angle.loc[(trueE >= ebins[i]) &\
                                   (trueE <= ebins[i+1])]
        N = len(angles_bin)

        quantiles[0, i] = angles_bin.quantile(q)
        # error of quantile follows binominal distribution
        quantiles[1, i] = np.sqrt(N * q * ( 1 - q)) / N

    # calculate mean positions
    pos_log = np.mean(np.array([ebins_log[:-1], ebins_log[1:]]), axis=0)
    pos = np.power(10, pos_log)
    # get asymmetrical bin widths
    err = [pos - ebins[:-1], ebins[1:] - pos]

    return (quantiles, pos, err)


def load_data(files):
    for file in tqdm(files, total=len(files)):
        try:
            datafile = pd.read_hdf(file, key="direction_reconstriction").iloc[:, [1, 6, 7]]
        except (HDF5ExtError, OSError):
            print("Not able to read {}".format(file))
            continue

        try:
            data = pd.concat([data, datafile])
        except NameError:
            data = datafile

    return data

def add_requirement():
    loge = [-1.64983, -1.49475, -1.32191, -1.05307, -0.522689,
            0.139036, 0.949169, 1.67254, 2.20447, 2.49232]
    e = np.power(10, loge)
    angres = [0.453339, 0.295111, 0.203515, 0.138619, 0.0858772, 0.0569610, 0.0372988, 0.0274391, 0.0232297, 0.0216182]

    plt.plot(e, angres, linewidth=4, label="requirment", color="k", alpha=0.5, linestyle="--")


def plot_all(data_dict, offsets, names, odir, plotname, outname):
    # plot everybin in same plot
    plt.figure(figsize=(14, 10))
    rcParams['xtick.labelsize'] = 15
    rcParams['ytick.labelsize'] = 15
    plt.xscale('log')

    for ii, offset in enumerate(offsets[:-1]):
        for name in names:

            data = data_dict[name].query("offset > {} and offset <  {}".format(offsets[ii], offsets[ii + 1]))

            res = calc_angular_resolution(off_angle=data.off_angle, trueE=data.MC_Energy,
                                          erange=[0.008, 700], bins=30)

            if offsets == [-1, 100]:
                label = name
            else:
                label = "offset {} {}".format(offsets[ii], offsets[ii + 1])
            if name == "default":
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="C{}".format(ii),
                             label="", linewidth=4, markersize=2, alpha=0.4, linestyle='--')
            else:
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="C{}".format(ii),
                             label=label, linewidth=4, markersize=2, alpha=0.7)

    add_requirement()
    plt.xlabel("True Energy / TeV", fontsize=20)
    plt.ylabel("Angular resolution / deg", fontsize=20)
    plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
    plt.legend(fontsize=20)
    plt.ylim([-0.1, 0.6])
    plt.tight_layout()

    if outname == "None":
        plt.savefig("{}/Angle_all_{}.pdf".format(odir, plotname))
    else:
        plt.savefig("{}/{}".format(odir, outname))
    plt.close()

def plot_improvement(data_dict, offsets, names, odir, plotname, outname):
    # plot everybin in same plot
    plt.figure(figsize=(14, 10))
    rcParams['xtick.labelsize'] = 15
    rcParams['ytick.labelsize'] = 15
    plt.xscale('log')

    for name in names:
        if name == "default":
            continue

         if offsets == [-1, 100]:
             label = name
         else:
             label = "offset {} {}".format(offsets[ii], offsets[ii + 1])

        for ii, offset in enumerate(offsets[:-1]):
            res_dict = {}

            data = data_dict[name].query("offset > {} and offset <  {}".format(
                                            offsets[ii], offsets[ii + 1]))
            res_dict[name] = calc_angular_resolution(off_angle=data.off_angle,
                                                    trueE=data.MC_Energy,
                                                    erange=[0.008, 700], bins=30)

            data_def = data_dict["default"].query("offset > {} and offset < {}".format(
                                            offsets[ii], offsets[ii + 1]))
            res_dict["default"] = calc_angular_resolution(off_angle=data_def.off_angle,
                                                    trueE=data_def.MC_Energy,
                                                    erange=[0.008, 700], bins=30)

            resolution = un.uarray(res_dict[name][0][0], res_dict[name][0][1])
            default = un.uarray(res_dict["default"][0][0], res_dict["default"][0][1])
            improvement = 1 - (resolution / default)
            imp_val = un.nominal_values(improvement)
            imp_err = un.std_devs(improvement)

            plt.errorbar(res_dict["default"][1], imp_val, zorder=10, color="C{}".format(ii),
                         label=label, linewidth=4, markersize=2, alpha=0.7, fmt="o--")

            plt.fill_between(res_dict["default"][1], imp_val - imp_err, imp_val + imp_err,
                             color="C{}".format(ii), alpha = 0.2)


        plt.xlabel("True Energy / TeV", fontsize=20)
        plt.ylabel("Relative improvement of angular resolution", fontsize=20)
        plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        plt.legend(fontsize=20)
        plt.grid(axis="y")
        plt.ylim([-0.2, 0.65])
        plt.tight_layout()

        if outname == "None":
            plt.savefig("{}/Angle_improvement_{}{}.pdf".format(odir, name, plotname))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()

def plot_per_name(data_dict, offsets, names, odir, outname):

    for name in names:
        # plot everybin in same plot
        plt.figure(figsize=(14, 10))
        rcParams['xtick.labelsize'] = 15
        rcParams['ytick.labelsize'] = 15
        plt.xscale('log')

        plotname = ""
        for ii, offset in enumerate(offsets[:-1]):
            plotname += "_{}".format(offset)
            data = data_dict[name].query("offset > {} and offset <  {}".format(offsets[ii], offsets[ii + 1]))

            res = calc_angular_resolution(off_angle=data.off_angle, trueE=data.MC_Energy,
                                          erange=[0.008, 700], bins=30)

            if offsets == [-1, 100]:
                label = name
            else:
                label = "offset {} {}".format(offsets[ii], offsets[ii + 1])

            plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="C{}".format(ii),
                         label=label, linewidth=4, markersize=2, alpha=0.7)

        add_requirement()
        plt.xlabel("True Energy / TeV", fontsize=20)
        plt.ylabel("Angular resolution / deg", fontsize=20)
        plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        plt.legend(fontsize=20)
        plt.ylim([-0.1, 0.6])
        plt.tight_layout()

        if outname == "None":
            plt.savefig("{}/Angular_per_type_{}.pdf".format(odir, name))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()

def plot_per_offbin(data_dict, offsets, names, odir, outname):

    for ii, offset in enumerate(offsets[:-1]):
        # plot everybin in same plot
        plt.figure(figsize=(14, 10))
        rcParams['xtick.labelsize'] = 15
        rcParams['ytick.labelsize'] = 15
        plt.xscale('log')

        plotname = ""
        for name in names:
            plotname += "_{}".format(name)
            data = data_dict[name].query("offset > {} and offset <  {}".format(offsets[ii], offsets[ii + 1]))

            res = calc_angular_resolution(off_angle=data.off_angle, trueE=data.MC_Energy,
                                          erange=[0.008, 700], bins=30)

            if name == "default":
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="k",
                             label=name, linewidth=4, markersize=2, alpha=0.5)
            else:
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10,
                             label=name, linewidth=4, markersize=2, alpha=0.7)

        add_requirement()
        plt.xlabel("True Energy / TeV", fontsize=20)
        plt.ylabel("Angular resolution / deg", fontsize=20)
        plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        plt.legend(fontsize=20)
        plt.ylim([-0.1, 0.6])
        plt.tight_layout()

        if outname == "None":
            plt.savefig("{}/Angular_per_offbin{}_{}_{}.pdf".format(odir, plotname, offsets[ii], offsets[ii + 1]))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir' , default="/lustre/fs19/group/cta/users/kpfrang/software/ctapipe_output/")
    parser.add_argument('--directories', nargs='*', required=True)
    parser.add_argument('--names', nargs='*', required=True)
    # parser.add_argument('--type', nargs='*', required=True)
    parser.add_argument('--odir', default="./AngularResolution")
    parser.add_argument('--outname', default="None")
    parser.add_argument('--offsets', nargs="*", default=[-1, 100], type=float)

    args = parser.parse_args()


    for offset in args.offsets:
        try:
            fname += "_{}".format(offset)
        except NameError:
            fname = str(offset)

    odir = "{}/{}".format(args.odir, fname)

    if not (os.path.isdir(odir)):
        os.makedirs(odir)

    data_dict = {}
    for directory, name in zip(args.directories, args.names):
        datadir = os.path.abspath("{}/{}".format(args.basedir, directory))
        print("Loading files from directory '{}'.".format(datadir))
        files = glob.glob("{}/output*.h5".format(datadir))
        data_dict[name] = load_data(files)


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



    # plot everybin in same plot
    #plot_all(data_dict, args.offsets, args.names, odir, plotname, args.outname)

    ################################
    # one plot for each name
    plot_per_name(data_dict, args.offsets, args.names, odir, args.outname)

    ################################
    plot_per_offbin(data_dict, args.offsets, args.names, odir, args.outname)

    if (len(args.names) >= 2) & ("default" in args.names):
        ################################
        # improvement over default
        plot_improvement(data_dict, args.offsets, args.names, odir, plotname, args.outname)
