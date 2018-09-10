"""
Generate one plot for each offset bin.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .plotting_tools import calc_angular_resolution, add_requirement


def plot_per_offbin(data_dict, offsets, names, odir, outname):

    for ii, offset in enumerate(offsets[:-1]):
        # plot everybin in same plot
        plt.figure(figsize=(14, 10))
        rcParams['xtick.labelsize'] = 15
        rcParams['ytick.labelsize'] = 15
        plt.xscale('log')

        plotname = ""
        for jj, name in enumerate(names):
            plotname += "_{}".format(name)
            data = data_dict[name].query("offset > {} and offset <  {}".format(offsets[ii], offsets[ii + 1]))

            res = calc_angular_resolution(off_angle=data.off_angle, trueE=data.MC_Energy,
                                          erange=[0.015, 500], bins=30)

            if name == "default":
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="k",
                             label=name, linewidth=4, markersize=2, alpha=0.5)
            else:
                if offsets == [-1, 100]:
                    color = "C{}".format(jj + 1)
                else:
                    color = "C{}".format(jj)
                plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10,
                             label=name, linewidth=4, markersize=2, alpha=0.7, color=color)

        add_requirement()
        plt.xlabel("True Energy / TeV", fontsize=20)
        plt.ylabel("Angular Resolution / deg", fontsize=20)
        #plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        if offsets == [-1, 100]:
            plt.title("Point like simulations")
        else:
            plt.title("{}$^\circ$ < offset angle < {}$^\circ$".format(offsets[ii], offsets[ii + 1]), fontsize=20)
        plt.legend(fontsize=20)
        plt.ylim([-0.1, 0.6])
        plt.tight_layout()

        if outname == "None":
            if offsets == [-1, 100]:
                plt.savefig("{}/Angular_per{}_point.pdf".format(odir, plotname))
            else:
                plt.savefig("{}/Angular_per_offbin{}_{}_{}.pdf".format(odir, plotname, offsets[ii], offsets[ii + 1]))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()