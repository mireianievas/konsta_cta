"""
Plot the improvement of LUT methods toward the default weighting.
"""

from uncertainties import unumpy as un
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .plotting_tools import calc_angular_resolution

def plot_improvement(data_dict, offsets, names, odir, plotname, outname):
    # plot everybin in same plot
    plt.figure(figsize=(14, 10))
    rcParams['xtick.labelsize'] = 15
    rcParams['ytick.labelsize'] = 15
    plt.xscale('log')

    for name in names:
        if name == "default":
            continue

        for ii, offset in enumerate(offsets[:-1]):
            if offsets == [-1, 100]:
                label = name
            else:
                label = "offset {} {}".format(offsets[ii], offsets[ii + 1])

            res_dict = {}

            data = data_dict[name].query("offset > {} and offset <  {}".format(
                                            offsets[ii], offsets[ii + 1]))
            res_dict[name] = calc_angular_resolution(off_angle=data.off_angle,
                                                    trueE=data.MC_Energy,
                                                    erange=[0.015, 500], bins=30)

            data_def = data_dict["default"].query("offset > {} and offset < {}".format(
                                            offsets[ii], offsets[ii + 1]))
            res_dict["default"] = calc_angular_resolution(off_angle=data_def.off_angle,
                                                    trueE=data_def.MC_Energy,
                                                    erange=[0.015, 500], bins=30)

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
        #plt.title(r"$N_{images}>4$, $N_{images, LST}>2$, $N_{images, MST}>2$, $N_{images, SST}>4$", fontsize=20)
        plt.legend(fontsize=20)
        plt.grid(axis="y")
        plt.ylim([-0.2, 0.65])
        plt.tight_layout()

        if outname == "None":
            plt.savefig("{}/Angle_improvement_{}{}.pdf".format(odir, name, plotname))
        else:
            plt.savefig("{}/{}".format(odir, outname))
        plt.close()