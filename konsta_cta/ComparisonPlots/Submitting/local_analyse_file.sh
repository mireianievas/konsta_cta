#!/bin/zsh
#
#(otherwise the default shell would be used)
#$ -S /bin/zsh

# source .zshrc (must specifiy the correct python version)
source $HOME/.zshrc

# read the inputs
FILE=$1
RUN=$2 
DTYPE=$3
ODIR=$4

echo "Will use python version "
which python
#echo "with these installes packages:"
conda list
echo "--------------- Start of analysis ---------------"
# execute the analysis
python /afs/ifh.de/user/k/kpfrang/scratch/software/konsta_cta/konsta_cta/ComparisonPlots/Submitting/one_file.py --filepath $FILE --odir $ODIR --run $RUN --dataType $DTYPE