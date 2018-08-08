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
#$ -l h_rss=15G
#
#$ -l tmpdir_size=30G
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
ZENITH=$3
DIRECTION=$4
DTYPE=$5
ODIR=$6
INTEGRATOR=$7
CLEANER=$8
TELS=$9

cd ~/scratch/software/konsta_cta/konsta_cta/ComparisonPlots/Submitting

echo "Will use python version "
which python
#echo "with these installes packages:"
#conda list
echo "--------------- Start of analysis ---------------"
# execute the analysis
python /afs/ifh.de/user/k/kpfrang/scratch/software/konsta_cta/konsta_cta/ComparisonPlots/Submitting/one_file.py --filepath $FILE --odir $ODIR --run $RUN --zenith $ZENITH --direction $DIRECTION --dataType $DTYPE --integrator $INTEGRATOR --cleaner $CLEANER --tels $TELS
