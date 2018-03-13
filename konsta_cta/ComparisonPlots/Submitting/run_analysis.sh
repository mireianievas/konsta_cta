#!/bin/bash

##########################
# execute submit_file.py #
##########################

# need to run zsh first so oh_my_zsh can be sourced by .zshrc (why?)
#zsh
#source $HOME/.zshrc


python submit_file.py --listGAMMA runlist_comparison_gamma_onSource_100.list --listNSB runlist_comparison_NSB.list --submit false --qsub false --concatenate true --odir /lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis