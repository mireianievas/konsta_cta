import glob
import os
import argparse

import pandas as pd
import numpy as np
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
            datafile = pd.read_hdf(file, key="direction_reconstriction").iloc[:, [1, 6]]
            data = pd.concat([data, datafile])
        except NameError:
            data = datafile
        except (HDF5ExtError, OSError):
            print("Not able to read {}".format(file))
            continue

    return data

def add_requirement():
    loge = [-1.64983, -1.49475, -1.32191, -1.05307, -0.522689,
            0.139036, 0.949169, 1.67254, 2.20447, 2.49232]
    e = np.power(10, loge)
    angres = [0.453339, 0.295111, 0.203515, 0.138619, 0.0858772, 0.0569610, 0.0372988, 0.0274391, 0.0232297, 0.0216182]

    plt.plot(e, angres, linewidth=4, label="requirment", color="k", alpha=0.5, linestyle="--")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir' , default="/lustre/fs19/group/cta/users/kpfrang/software/ctapipe_output/diffuse")
    parser.add_argument('--directories', nargs='*', required=True)
    parser.add_argument('--names', nargs='*', required=True)
    parser.add_argument('--odir', default="./AngularResolution")

    args = parser.parse_args()

    plt.figure(figsize=(14, 10))
    rcParams['xtick.labelsize'] = 15
    rcParams['ytick.labelsize'] = 15
    plt.xscale('log')

    for directory, name in zip(args.directories, args.names):
        print("Loading files from directory '{}'.".format(directory))
        datadir = os.path.abspath("{}/{}".format(args.basedir, directory))
        files = glob.glob("{}/output*.h5".format(datadir))
        data = load_data(files)
        res = calc_angular_resolution(off_angle=data.off_angle, trueE=data.MC_Energy,
                                      erange=[0.008, 700], bins=30)

        plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10,
                     label=name, linewidth=4, markersize=2, alpha=0.7)

    add_requirement()
    plt.xlabel("True Energy / TeV", fontsize=20)
    plt.ylabel("Angular resolution / deg", fontsize=20)
    plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
    plt.legend(fontsize=20)
    plt.tight_layout()
    plt.savefig("{}/Angular_resolution_def_LUT_double.pdf".format(args.odir))