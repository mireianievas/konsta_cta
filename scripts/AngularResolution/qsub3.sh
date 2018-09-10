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

source $HOME/.zshrc

python ./angular_resolution.py --directories $1 $2 $3 --names $4 $5 $6 --odir $7 --offsets 0.0 2.0 6.0 10.0 --maxfiles $8