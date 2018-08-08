import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def get_norm_factor(values):
    norm = np.sum(values) * ((len(values) -1) / len(values))
    return norm

def print_stat_error(bins, value, color=None, alpha=1, add=True, normed=False):
    '''
    input
    -----
    bins - position of bins
    value - values of unbinned histogram
    '''
    if add:
        value = np.append(value, value[-1])
    norm = get_norm_factor(value)
    error = np.sqrt(value)
    if normed:
        error = error / norm
        value = value / norm
    plt.fill_between(x=bins, y1=value+error, y2=value-error, edgecolor=None, step="post", alpha=alpha, color=color)



def change_binning(histo, number_to_sum):
    histogram = np.array(histo.hists)
    hist_sum = None
    for k in range(number_to_sum):
        try:
            entries = len(histogram[k::number_to_sum])
            if entries == len(hist_sum):
                hist_sum = hist_sum + histogram[k::number_to_sum]
            else:
                hist_sum = hist_sum[:entries] + histogram[k::number_to_sum]
        except (NameError, TypeError):
            hist_sum = histogram[::number_to_sum]

    hist_sum = np.append(hist_sum[0], hist_sum)
    hist_sum = np.append(0, hist_sum)
    bins_ED =  np.append(histo.bins[0], histo.bins[::number_to_sum])

    return bins_ED, hist_sum

def plot_numTELSvsENERGY(number_images, EventDisplay, EventDisplay_raw, save=None, compare=None, hyp_stand="hyper"):
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

    # core distance
    number_images["core_dist"] = np.sqrt(number_images.core_x**2 + number_images.core_y**2)

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
    #ax.set_xlabel("trigger level", fontsize=15)
    #ax.set_ylabel("image cleaning", fontsize=15)
    #plt.colorbar(scatter, ax=ax, label='E$_{MC}$')
    #plt.style.use(['default'])
    #plt.tight_layout()
    #plt.savefig(save+"_2D.pdf")
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
    ax.set_ylabel("$N_{trigger} - N_{cleaning}$", fontsize=15)
    plt.colorbar(scatter, ax=ax)
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2Dhist_difference.pdf")
    plt.close()

    mask = number_images.all_images != 0
    # 2D hist ratio
    ratio = np.array(number_images.cleaned)[mask]/np.array(number_images.all_images)[mask]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.hist2d(number_images.Emc_log[mask], ratio, bins=40,
        cmap='viridis', norm=LogNorm())
    ax.set_xlabel("log(E$_{MC})$ / TeV", fontsize=15)
    ax.set_ylabel("$N_{cleaning} / N_{trigger}$", fontsize=15)
    plt.colorbar(scatter, ax=ax)
    plt.style.use(['default'])
    plt.tight_layout()
    plt.savefig(save+"_2Dhist_ratio.pdf")
    plt.close()



         #####  #########
        ######  ###     ###
       ### ###  ###      ###
     ###   ###  ###       ###
           ###  ###       ###
           ###  ###       ###
           ###  ###      ###
           ###  ###     ###
           ###  #########


    # Plot 1D Histograms for each Energy bin

    # range between 10Gev and 100TeV
    x = np.linspace(-2, 2, 5)

    for i in range(len(x) - 1):
        number_bin = number_images[((number_images.Emc_log >= x[i]) &
                                    (number_images.Emc_log <= x[i + 1]))]
        fig = plt.figure()
        if max(number_bin.cleaned) <= 20:
            binsize = 1
        if (max(number_bin.cleaned) > 20) & (max(number_bin.cleaned) <= 70):
            binsize = 2
        if (max(number_bin.cleaned) > 70):
            binsize = 3
        if (max(number_bin.cleaned) > 140):
            binsize = 5
        if (max(number_bin.cleaned) > 200):
            binsize = 7

        bins = range(0, int(max(number_bin.cleaned)) + binsize, binsize)
        for number, label, col in zip([number_bin.all_images, number_bin.cleaned], ["trigger", "cleaned"], ["C0", "C1"]):
            plt.hist(number, bins=bins, histtype='step', label=label,
                     log=False, linewidth=2, alpha=0.8, color=col)
            if label == "trigger":
                plt.hist(number, bins=bins, histtype='bar',
                     log=False, linewidth=0, alpha=0.05)
                
        plt.title("Energy range ({:.3f}, {:.3f})".format(x[i], x[i+1]), fontsize=18)
        plt.xlabel("Number of images per event", fontsize=15)
        plt.ylabel("Number of events", fontsize=15)
        plt.legend(fontsize=15)
        plt.tight_layout()
        plt.savefig(save+"_1Dhists_{:.3f}_{:.3f}.pdf".format(x[i], x[i+1]))
        plt.style.use("default")
        plt.close()

####################################################################################
        ####################################################################        
                ####################################################                                                    
                        ####################################        
                                ####################        
                                        ####        


    # range between 10Gev and 100TeV
    x = np.linspace(-2, 2, 5)

    if hyp_stand == "hyper":
        histos = [EventDisplay, EventDisplay_raw]
        levels = ["cleaned", "all_images"]
        labels = ["cleaning", "raw"] 
    elif hyp_stand == "standard":
        histos = [EventDisplay]
        levels = ["cleaned"]
        labels = ["cleaning"]


    for EventDisplay_histograms, level, label in zip(histos, levels, labels):
        '''
        for i, EDisp in zip(range(len(x) - 1), ["nimages_ebin1", "nimages_ebin2",
                                                "nimages_ebin3", "nimages_ebin4"]):
            ED_hist = EventDisplay_histograms[EDisp]

            number_bin = number_images[((number_images.Emc_log >= x[i]) &
                                        (number_images.Emc_log <= x[i + 1]))]
            fig = plt.figure()
            ax = fig.add_subplot(111)

            binsize = 1
            bins = range(0, int(max(number_bin[level])) + binsize, binsize)
            number = number_bin[level]
            ax.hist(number, bins=bins, histtype='step', label="ctapipe",
                     log=False, linewidth=2, alpha=0.8, color="C0")

            ax.plot(ED_hist.bins, ED_hist.hists, ls='steps', linewidth=2,
                    label="EventDisplay", color="C1", alpha=0.8)
                    
            plt.title("{}, energy range ({:.3f}, {:.3f})".format(label, x[i], x[i+1]), fontsize=18)
            ax.set_xlabel("Number of images per event", fontsize=15)
            ax.set_ylabel("Number of events", fontsize=15)
            plt.legend(fontsize=15)
            plt.tight_layout()
            plt.savefig(compare+"{}_{:.3f}_{:.3f}.pdf".format(label, x[i], x[i+1]))
            plt.style.use("default")
            plt.close()
        '''
        

        #nimages_energy = ["nimages_ebin1", "nimages_ebin2", "nimages_ebin3", "nimages_ebin4"]
        #ntriger_energy = ["ntrigimages_ebin1", "ntrigimages_ebin2", "ntrigimages_ebin3", "ntrigimages_ebin4"]
        #
        #for trig_im, label_2 in zip([nimages_energy, ntriger_energy], ["ntrigimages", "ntrigger"])

        # range between 10Gev and 100TeV log scale
        x = np.linspace(-2, 2, 5)

        for i, EDisp in zip(range(len(x) - 1), ["nimages_ebin1", "nimages_ebin2",
                                                "nimages_ebin3", "nimages_ebin4"]):
            ED_hist = EventDisplay_histograms[EDisp]
            ED_hist = ED_hist.dropna()
            number_bin = number_images[((number_images.Emc_log >= x[i]) &
                                        (number_images.Emc_log <= x[i + 1]))]
            print("({}, {}): ED - {}.  |  ctapipe - {}".format(
                x[i], x[i+1], np.sum(ED_hist), len(number_bin)))

            fig = plt.figure()
            ax = fig.add_subplot(111)

            #if EDisp == "nimages_ebin3":
            #    number_to_sum = 2
            #elif EDisp == "nimages_ebin4":
            #    number_to_sum = 5
            #else:
            #    number_to_sum = 1

            number_to_sum = 4
            bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

            bins = np.arange(0, np.max(number_bin[level]) + (number_to_sum * ED_hist.width[0]),
                            number_to_sum * ED_hist.width[0])
            #binsize = 1
            #bins = range(0, int(max(number_bin.cleaned)) + binsize, binsize)
            number = number_bin[level]
            n, bins, p = ax.hist(number, bins=bins, histtype='step', label="ctapipe",
                     log=True, linewidth=2, alpha=0.8, color="C0")
            print_stat_error(bins, n, color="C0", alpha=0.4)

            #mask = np.isfinite(np.array(ED_hist.hists))
            #print(np.log10(ED_hist.hists[mask]))
            ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
                    label="EventDisplay", color="C1", alpha=0.8)
            plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), edgecolor=None, color="C1", alpha=0.4, step="pre")
            
            if int(x[i]) == -2:
                plt.title("(10 GeV, 100 GeV)", fontsize=18)
            elif int(x[i]) == -1:
                plt.title("(100 GeV, 1 TeV)", fontsize=18)
            elif int(x[i]) == 0:
                plt.title("(1 TeV, 10 TeV)", fontsize=18)
            elif int(x[i]) == 1:
                plt.title("(10 TeV, 100 TeV)", fontsize=18)
            ax.set_xlabel("Images per event", fontsize=15)
            ax.set_ylabel("Number of events", fontsize=15)
            plt.legend(fontsize=15)
            plt.tight_layout()
            plt.savefig(compare+"energy_{}_{:.3f}_{:.3f}_log.pdf".format(label, x[i], x[i+1]))
            plt.style.use("default")
            plt.close()


        
        # range between 10Gev and 100TeV log scale
        ecore = np.linspace(0, 2000, 5)

        for i, EDisp in zip(range(len(x) - 1), ["nimages_corebin1", "nimages_corebin2",
                                                "nimages_corebin3", "nimages_corebin4"]):
            ED_hist = EventDisplay_histograms[EDisp]
            ED_hist = ED_hist.dropna()
            number_bin = number_images[((number_images.core_dist >= ecore[i]) &
                                        (number_images.core_dist <= ecore[i + 1]))]
            fig = plt.figure()
            ax = fig.add_subplot(111)

            #if (EDisp == "nimages_corebin1")|(EDisp == "nimages_corebin2"):
            #    number_to_sum = 3
            #elif EDisp == "nimages_corebin4":
            #    number_to_sum = 1
            #else:
            #    number_to_sum = 1
            number_to_sum = 4
            bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

            bins = np.arange(0, np.max(number_bin[level]) + (number_to_sum * ED_hist.width[0]),
                            number_to_sum * ED_hist.width[0])
            #binsize = 1
            #bins = range(0, int(max(number_bin.cleaned)) + binsize, binsize)
            number = number_bin[level]
            n, bins, p = ax.hist(number, bins=bins, histtype='step', label="ctapipe",
                     log=True, linewidth=2, alpha=0.8, color="C0")
            print_stat_error(bins, n, color="C0", alpha=0.4)

            #mask = np.isfinite(np.array(ED_hist.hists))
            #print(np.log10(ED_hist.hists[mask]))
            ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
                    label="EventDisplay", color="C1", alpha=0.8)
            plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), edgecolor=None, color="C1", alpha=0.4, step="pre")
            
            plt.title("core range ({:.0f} m, {:.0f} m)".format(ecore[i], ecore[i+1]), fontsize=18)
            ax.set_xlabel("Number of images per event", fontsize=15)
            ax.set_ylabel("Number of events", fontsize=15)
            plt.legend(fontsize=15)
            plt.tight_layout()
            plt.savefig(compare+"core_{}_{:.3f}_{:.3f}_log.pdf".format(label, ecore[i], ecore[i+1]))
            plt.style.use("default")
            plt.close()

    
    for i, EDisp in zip(range(len(x) - 1), ["nimages_ebin1", "nimages_ebin2",
                                            "nimages_ebin3", "nimages_ebin4"]):
        
        ED_hist_cleaned = EventDisplay[EDisp]
        ED_hist_raw = EventDisplay_raw[EDisp]
        ED_hist = ED_hist_raw
        ED_hist.hists = ED_hist.hists - ED_hist_cleaned.hists

        ED_hist = ED_hist.dropna()

        number_bin = number_images[((number_images.Emc_log >= x[i]) &
                                    (number_images.Emc_log <= x[i + 1]))]
        fig = plt.figure()
        ax = fig.add_subplot(111)

        #if EDisp == "nimages_ebin3":
        #    number_to_sum = 2
        #elif EDisp == "nimages_ebin4":
        #    number_to_sum = 5
        #else:
        #    number_to_sum = 1

        number_to_sum = 4
        bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

        bins = np.arange(0, np.max(number_bin["all_images"] - number_bin["cleaned"]) + (number_to_sum * ED_hist.width[0]),
                        number_to_sum * ED_hist.width[0])
        #binsize = 1
        #bins = range(0, int(max(number_bin.cleaned)) + binsize, binsize)
        number = number_bin[level]
        n, bins, p = ax.hist(number, bins=bins, histtype='step', label="ctapipe",
                 log=True, linewidth=2, alpha=0.8, color="C0")
        print_stat_error(bins, n, color="C0", alpha=0.4)

        #mask = np.isfinite(np.array(ED_hist.hists))
        #print(np.log10(ED_hist.hists[mask]))
        ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
                label="EventDisplay", color="C1", alpha=0.8)
        plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), edgecolor=None, color="C1", alpha=0.4, step="pre")
        
        plt.title("energy log({:.0f} TeV, {:.0f} TeV)".format(x[i], x[i+1]), fontsize=18)
        ax.set_xlabel("Number of images not surviving cleaning", fontsize=15)
        ax.set_ylabel("Number of events", fontsize=15)
        plt.legend(fontsize=15)
        plt.tight_layout()
        plt.savefig(compare+"energy_difference_{:.0f}_{:.0f}_log.pdf".format(x[i], x[i+1]))
        plt.style.use("default")
        plt.close()
