"""
Plot all loaded results in one plot. This might look rather messy.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .plotting_tools import calc_angular_resolution, add_requirement

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
                                          erange=[0.015, 500], bins=30)

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
    plt.ylabel("Angular Resolution / deg", fontsize=20)

    if offsets == [-1, 100]:
        plt.title("Point like simulations")
    plt.legend(fontsize=20)
    plt.ylim([-0.1, 0.6])
    plt.tight_layout()

    if outname == "None":
        plt.savefig("{}/Angle_all_{}.pdf".format(odir, plotname))
    else:
        plt.savefig("{}/{}".format(odir, outname))
    plt.close()