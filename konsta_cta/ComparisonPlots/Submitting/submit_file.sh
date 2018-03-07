#!/bin/bash -x

# Source my .bashrc, is properly "installed"
source $HOME/.zshrc

FILE = $1
RUN = $2 
DTYPE = $3
ODIR = $4

python one_file.py --filepath $FILE --odir $ODIR --run $RUN --dataType $DTYPE