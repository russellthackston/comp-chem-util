START=0
COUNTER=0
while read p; do
  END=$p
  COUNTER=$[COUNTER + 1]
  mkdir chunk-$COUNTER
  pushd chunk-$COUNTER
  /usr/bin/time -v -o time.out python ../taylor.py -s $START -e $END 5 99 &
  popd
  START=$END
done <indexes.txt

