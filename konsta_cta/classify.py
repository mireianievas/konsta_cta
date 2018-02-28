import numpy as np


class EventClassifier():
    '''Classification of events

    Discrimination of gamma ray and	hadron induced
    images in the cameras.
    '''

    def __init__(self, gammas=None, protons=None):
        if ((not gammas) or (not protons)):
         	raise ValueError("Gamma and proton data must be given")
        self.gammas = gammas
        self.protons = protons

        # split dataset to training and application.
    def split_data(self, gamma_list=None, proton_list=None, fraction=0.1):
        # Input:
        # list of links to gamma and proton file
        # fraction of files to use for training
        ########

        if ((not gamma_list) or (not proton_list)):
            gamma_list = np.array(self.gammas.file_list)
            proton_list = np.array(self.protons.file_list)
        else:
            pass

        n_gamma = len(gamma_list)
        n_proton = len(proton_list)
        for par in [n_gamma, n_proton]:
            if par < 2:
                raise ValueError("Needs at least a list 2 runs.")
        # use only fraction of the files for training
        n_train_gamma = int(fraction * n_gamma)
        n_train_proton = int(fraction * n_proton)

        if n_train_gamma == 0:
        	n_train_gamma = 1
        if n_train_proton == 0:
        	n_train_proton = 1

        # random selection of the files to use for training
        sample_index_gamma = np.random.choice(n_gamma, n_train_gamma)
        sample_index_proton = np.random.choice(n_proton, n_train_proton)

        self.gamma_train = gamma_list[sample_index_gamma]
        self.proton_train = proton_list[sample_index_proton]

        self.gamma_test = np.delete(gamma_list, sample_index_gamma)
        self.proton_test = np.delete(proton_list, sample_index_proton)
