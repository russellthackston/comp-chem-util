DISPLACEMENTS=$(cat disp.dat)
D_ARRAY=(${DISPLACEMENTS//,/ })
for i in "${D_ARRAY[@]}"
do
   echo $i
done
