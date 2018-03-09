#!/bin/bash -x


# source .zshrc
zsh
source $HOME/.zshrc

source activate cta-dev

# read the inputs
FILE=$1
RUN=$2 
DTYPE=$3
ODIR=$4

# execute the analysis
python -q one_file.py --filepath $FILE --odir $ODIR --run $RUN --dataType $DTYPE