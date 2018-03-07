#!/bin/bash -x

# Source my .zshrc
source $HOME/.zshrc

# read the inputs
FILE = $1
RUN = $2 
DTYPE = $3
ODIR = $4

# execute the analysis
python one_file.py --filepath $FILE --odir $ODIR --run $RUN --dataType $DTYPE