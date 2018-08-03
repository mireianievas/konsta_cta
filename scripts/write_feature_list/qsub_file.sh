#!/bin/zsh
#
#(otherwise the default shell would be used)
#$ -S /bin/zsh
#
#(stderr and stdout are merged together to stdout)
#$ -j y
#
#(Name of the process)
#$ -N ana_run
#
#$ -l h_cpu=11:29:00
#
#(the maximum memory usage of this job)
#$ -l h_rss=10G
#
#$ -l tmpdir_size=20G
#
#$ -P cta
#$ -js 9
#
#(use scientific linux 7)
#$ -l os=sl7

# Sourcing .zshrc and conda environment for ctapipe to
# ensure that the correct package versions are used.
source $HOME/.zshrc
source activate cta-dev

# read inputs
FILE=$1
OUTPUTFILE=$2
TELS=$3
DIR=$4
CTAPIPE_AUX_DIR=$5
CONFIG=$6

echo "Will use python installation:"
which python

echo "\n--------------- Start of analysis ---------------"
# execute the analysis
python $DIR/analyse_file_write_list.py --filepath $FILE --outputfile $OUTPUTFILE --config $CONFIG --tels_to_use $TELS --ctapipe_aux_dir $CTAPIPE_AUX_DIR