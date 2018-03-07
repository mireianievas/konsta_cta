import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

def plot_numTELSvsENERGY(number_images, save=None):
    ''' Generate plot of number of images in telescopes
        in dependency of energy

        Input
        -----
        number_images - pandas.DataFrame with columns
                            Emc - MC energy of event
                            all_images - # all images
                            cleaned - # cleaned images
    '''
    # log energy
    number_images["Emc_log"] = np.log10(number_images.Emc)
    x = np.linspace(min(number_images.Emc_log),
                    max(number_images.Emc_log), 20)
    means_all = []
    stds_all = []
    means_clean = []
    stds_clean = []
    for i in range(len(x) - 1):
        means_all.append(number_images[((number_images.Emc_log >= x[i]) &
                 (number_images.Emc_log <= x[i + 1]))].all_images.mean(0))
        stds_all.append(number_images[((number_images.Emc_log >= x[i]) &
                 (number_images.Emc_log <= x[i + 1]))].all_images.std(0))
        means_clean.append(number_images[((number_images.Emc_log >= x[i]) &
                 (number_images.Emc_log <= x[i + 1]))].cleaned.mean(0))
        stds_clean.append(number_images[((number_images.Emc_log >= x[i]) &
                 (number_images.Emc_log <= x[i + 1]))].cleaned.std(0))
    means_all = np.nan_to_num(means_all)
    stds_all = np.nan_to_num(stds_all)
    means_clean = np.nan_to_num(means_clean)
    stds_clean = np.nan_to_num(stds_clean)

    # x positions
    x_pos = np.power(10, ((x[:-1] + x[1:]) / 2))
    # back to non logscale
    x2 = np.power(10, x)
    # asyymetrical error for accurat display in log scale
    lower_error = abs(x2[:-1] - x_pos)
    upper_error = abs(x2[1:] - x_pos)
    error = [lower_error, upper_error]

    # plot result
    fig = plt.figure(figsize=[10, 7])
    ax = fig.add_subplot(111)
    ax.tick_params('both', labelsize=15)
    ax.errorbar(x_pos, means_all, xerr=error, yerr=stds_all,
    		fmt='o', alpha=0.7, label='trigger level')
    ax.errorbar(x_pos, means_clean, xerr=error, yerr=stds_clean,
    		fmt='o', alpha=0.7, label='image cleaning')
    ax.semilogx()
    ax.set_xlabel("E$_{MC}$ / TeV", fontsize=15)
    ax.set_ylabel("Telescopes with images", fontsize=15)
    ax.legend(loc='upper left', fontsize=15)
    
    plt.tight_layout()
    plt.savefig(save+".pdf")
    plt.close()

    # 2D scatter
    fig = plt.figure()
    ax = fig.add_subplot(111)
    scatter = ax.scatter(number_images.all_images, number_images.cleaned,
        c=number_images.Emc, cmap='viridis', s=1, norm=LogNorm())
    ax.set_xlabel("trigger level", fontsize=15)
    ax.set_ylabel("image cleaning", fontsize=15)
    plt.colorbar(scatter, ax=ax, label='E$_{MC}$')
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2D.pdf")
    plt.close()

    # 2D hist cleaned
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.hist2d(number_images.Emc_log, number_images.cleaned, bins=40,
        cmap='viridis', norm=LogNorm())
    ax.set_xlabel("log(E$_{MC})$ / TeV", fontsize=15)
    ax.set_ylabel("image cleaning", fontsize=15)
    plt.colorbar(scatter, ax=ax)
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2Dhist_cleaned.pdf")
    plt.close()    

    # 2D hist trigger
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.hist2d(number_images.Emc_log, number_images.all_images, bins=40,
        cmap='viridis', norm=LogNorm())
    ax.set_xlabel("log(E$_{MC})$ / TeV", fontsize=15)
    ax.set_ylabel("image cleaning", fontsize=15)
    plt.colorbar(scatter, ax=ax)
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2Dhist_trigger.pdf")
    plt.close()

    # 2D hist diff
    diff = number_images.all_images-number_images.cleaned
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.hist2d(number_images.Emc_log, diff, bins=[40,max(diff)],
        cmap='viridis', norm=LogNorm())
    ax.set_xlabel("log(E$_{MC})$ / TeV", fontsize=15)
    ax.set_ylabel("diff(trigger, cleaning)", fontsize=15)
    plt.colorbar(scatter, ax=ax)
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2Dhist_difference.pdf")
    plt.close()