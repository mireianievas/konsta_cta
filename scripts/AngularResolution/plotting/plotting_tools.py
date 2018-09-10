import numpy as np
import matplotlib.pyplot as plt

def calc_angular_resolution(off_angle, trueE, q=0.68, erange=[0.01, 100], bins=10):
    '''
    off_angle : pandas.Series
    true_e : pandas.Series
    quantile : float
    erange : list, tuple
        upper an lower edge in TeV
    ebins : int
        number of bins
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

def add_requirement():
    loge = [-1.64983, -1.49475, -1.32191, -1.05307, -0.522689,
            0.139036, 0.949169, 1.67254, 2.20447, 2.49232]
    e = np.power(10, loge)
    angres = [0.453339, 0.295111, 0.203515, 0.138619, 0.0858772, 0.0569610, 0.0372988, 0.0274391, 0.0232297, 0.0216182]

    plt.plot(e, angres, linewidth=4, label="requirement", color="k", alpha=0.5, linestyle="--")