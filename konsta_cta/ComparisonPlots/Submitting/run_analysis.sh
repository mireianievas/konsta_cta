#!/bin/bash

##########################
# execute submit_file.py #
##########################

# need to run zsh first so oh_my_zsh can be sourced by .zshrc (why?)
#zsh
#source $HOME/.zshrc

python submit_file.py --listGAMMA runlist_onSource.list --listNSB None --submit true --qsub false --concatenate false --odir ../Analysis_180209