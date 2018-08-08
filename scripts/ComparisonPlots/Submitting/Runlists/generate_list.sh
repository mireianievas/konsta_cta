# generate a runlist:
NAME="runlist_comparison"

number=100
PARTICLE=( "gamma_onSource" )
PARTICLE_type=( "gamma" )
CONE=( "" )
#PARTICLE=( "gamma_cone" "gamma_onSource" "electron" "proton" )
#PARTICLE_type=( "gamma" "gamma" "electron" "proton" )
#CONE=( "_cone10" "" "" "" )

if (( $number=='ALL' ))
then
for ((i = 0; i < ${#PARTICLE[@]}; i++ ))
do
	N=${PARTICLE[$i]}
        E=${PARTICLE_type[$i]}
        C=${CONE[$i]}
	find "/lustre/fs21/group/cta/prod3b/prod3b-paranal20deg/${N}/" -type f -name "${E}_20deg_*deg_run*___cta-prod3_desert-2150m-Paranal-merged${C}.simtel.gz" >| $NAME"_"${N}"_"$number.list
done 
else
for ((i = 0; i < ${#PARTICLE[@]}; i++ ))
do
	N=${PARTICLE[$i]}
	E=${PARTICLE_type[$i]}
	C=${CONE[$i]}
	rm -f ./$NAME"_"${N}.list
	for ((k = 1; k < $number+1; k++))
	do
		FNAME="/lustre/fs21/group/cta/prod3b/prod3b-paranal20deg/${N}/${E}_20deg_180deg_run${k}___cta-prod3_desert-2150m-Paranal-merged${C}.simtel.gz"
		echo $FNAME >> ./$NAME"_"${N}"_"$number.list
	done
done
fi
