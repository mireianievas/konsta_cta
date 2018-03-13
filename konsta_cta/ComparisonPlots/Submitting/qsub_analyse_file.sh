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
#$ -l h_rss=8G
#
#$ -l tmpdir_size=40G
#
#$ -P cta
#$ -js 9
#
#(use scientific linux 7)
#$ -l os=sl7

echo "---------------- Informations about submission options see: ----------------"
echo "- https://grid.ifca.es/wiki/Cluster/Usage/GridEngine#Memory_usage_above_5G -"
echo "----------------------------------------------------------------------------"
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