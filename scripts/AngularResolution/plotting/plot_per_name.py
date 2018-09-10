"""
generate one plot for each method loaded.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .plotting_tools import calc_angular_resolution, add_requirement

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
                                          erange=[0.015, 500], bins=30)

            if offsets == [-1, 100]:
                label = "point source"
            else:
                label = "offset {} {}".format(offsets[ii], offsets[ii + 1])

            plt.errorbar(res[1], res[0][0], res[0][1], res[2], fmt="o", zorder=10, color="C{}".format(ii),
                         label=label, linewidth=4, markersize=2, alpha=0.7)

        add_requirement()
        plt.xlabel("True Energy / TeV", fontsize=20)
        plt.ylabel("Angular Resolution / deg", fontsize=20)
        #plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        plt.title("weighting method: {}".format(name), fontsize=20)
        plt.legend(fontsize=20)
        plt.ylim([-0.1, 0.6])
        plt.tight_layout()

        if outname == "None":
            plt.savefig("{}/Angular_per_type_{}.pdf".format(odir, name))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()