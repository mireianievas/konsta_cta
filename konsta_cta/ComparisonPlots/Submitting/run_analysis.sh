#!/bin/bash

##########################
# execute submit_file.py #
##########################

# need to run zsh first so oh_my_zsh can be sourced by .zshrc (why?)
#zsh
#source $HOME/.zshrc


ODIR='/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_hyperarray/neighbors0_adapted_window'

# file with list or 'all' for Hyperarray
TELS='all'

# Set the trace integration method
METHODS='all' # 'default' or 'all'
# default means:		(NeighbourPeakIntegrator, NullWaveformCleaner)



#python submit_file.py --listGAMMA ./Runlists/gamma_onSource_0deg.list --tels_to_use $TELS --submit true --qsub true --concatenate false --odir $ODIR
#python submit_file.py --listGAMMA ./Runlists/gamma_onSource_180deg.list --tels_to_use $TELS --submit true --qsub true --concatenate false --odir $ODIR 
#python submit_file.py --listPROTON ./Runlists/proton_0deg.list --tels_to_use $TELS --submit true --qsub true --concatenate false --odir $ODIR
#python submit_file.py --listPROTON ./Runlists/proton_180deg.list --tels_to_use $TELS --submit true --qsub true --concatenate false --odir $ODIR


ODIR='/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_hyperarray/highNSB'
# High NSB
python submit_file.py --listhighNSB ./Runlists/gamma_0deg_180deg_NSBx5.list --tels_to_use $TELS --submit true --qsub true --concatenate false --odir $ODIR --methods $METHODS

