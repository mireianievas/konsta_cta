#!bin/bash

ODIR="./Plots"
<<<<<<< HEAD
DAY="180716"
=======
DAY="180417"
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6

rm -r ./HistEventDisplay
sh extractHists.sh

TELNUM="false"
CHARGE="false"
HILLAS="true"

##############
# Hyperarray #
##############

<<<<<<< HEAD
python plotting.py --odir="$ODIR/hyperarray/$DAY/new_tubes_ED" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_hyperarray/neighbors0_adapted_window" --EventDisplayDir "./HistEventDisplay/hyperarray/" --MARSDir "./Data/MARS/" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS
=======
python plotting.py --odir="$ODIR/hyperarray/$DAY/neighbors0_adapted_window" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_hyperarray/neighbors0_adapted_window" --EventDisplayDir "./HistEventDisplay/hyperarray/" --MARSDir "./MARS/" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS &
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6

############
# high NSB #
############

#python plotting.py --odir="$ODIR/LaPalma/$DAY/highNSB" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_LaPalma/highNSB" --EventDisplayDir "None" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS


##################
# standard array #
##################
# This ist currently not working, as the histogram names for EventDisplay vary and
# columns are missing compared to Hyperarray

#python plotting.py --odir="$ODIR/3HB9-FD/$DAY/neighbors0" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_3HB9-FD/neighbors0" --EventDisplayDir "./HistEventDisplay/standardarray/" --MARSDir "./MARS/" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS

# for different image cleanings
#if [[ "$TELNUM" == "true" || $HILLAS == "true" ]]
#then
#	python plotting.py --odir="$ODIR/3HB9-FD/$DAY/neighbors1" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_3HB9-FD/neighbors1" --EventDisplayDir "./HistEventDisplay/standardarray/" --MARSDir "./MARS/" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS &
#	python plotting.py --odir="$ODIR/3HB9-FD/$DAY/neighbors2" --datadir "/lustre/fs19/group/cta/users/kpfrang/CTAPIPE/Analysis_3HB9-FD/neighbors2" --EventDisplayDir "./HistEventDisplay/standardarray/" --MARSDir "./MARS/" --numTELS_ENERGY $TELNUM --charge_distributions $CHARGE --hillas $HILLAS 
#fi
