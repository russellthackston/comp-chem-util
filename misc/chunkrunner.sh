START=0
while read p; do
  END=$p
  echo "$START $END"
  mkdir chunk-$START
  pushd chunk-$START
  python ../taylor.py -s $START -e $END 5 99 &
  popd
  START=$END
done <indexes.txt

