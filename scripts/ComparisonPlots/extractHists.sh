#!bin/bash

ODIR='HistEventDisplay/standardarray'

mkdir -p ./$ODIR/gamma
mkdir -p ./$ODIR/proton

root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_cleanedimages_standardarray.root", "./HistEventDisplay/standardarray/gamma")'
root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_cleanedimages_standardarray.root", "./HistEventDisplay/standardarray/proton")'

ODIR='HistEventDisplay/hyperarray'

mkdir -p ./$ODIR/gamma
mkdir -p ./$ODIR/proton

root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_cleanedimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/gamma")'
root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_cleanedimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/proton")'


ODIR='HistEventDisplay/hyperarray/raw'

mkdir -p ./$ODIR/gamma
mkdir -p ./$ODIR/proton

<<<<<<< HEAD
 root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_rawimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/raw/gamma")'
 root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_rawimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/raw/proton")'
=======
root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_rawimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/raw/gamma")'
root -l -q 'h12ascii.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_rawimages_hyperarray_allfiles_withcoredist.root", "./HistEventDisplay/hyperarray/raw/proton")'

>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6


ODIR='HistEventDisplay/hyperarray/with_err'

mkdir -p ./$ODIR/gamma
mkdir -p ./$ODIR/proton
<<<<<<< HEAD
mkdir -p ./$ODIR/gamma_new_tubes

root -l -q 'h12ascii_errors.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_cleanedimages_hyperarray_allfiles_witherrors.root", "./HistEventDisplay/hyperarray/with_err/gamma")'
root -l -q 'h12ascii_errors.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_cleanedimages_hyperarray_allfiles_witherrors.root", "./HistEventDisplay/hyperarray/with_err/proton")'
root -l -q 'h12ascii_errors.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_ntubes.root", "./HistEventDisplay/hyperarray/with_err/gamma_new_tubes")'
=======

root -l -q 'h12ascii_errors.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_gamma_cleanedimages_hyperarray_allfiles_witherrors.root", "./HistEventDisplay/hyperarray/with_err/gamma")'
root -l -q 'h12ascii_errors.C("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/histograms_proton_cleanedimages_hyperarray_allfiles_witherrors.root", "./HistEventDisplay/hyperarray/with_err/proton")'
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6
