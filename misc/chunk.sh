if [[ $OSTYPE == *"linux"* ]]; then
	CORES=$(lscpu|grep 'CPU(s)'|head -n 1|tr -s ' '|cut -f 2 -d ' ')
else
        CORES=$(sysctl hw.ncpu | cut -f 2 -d ' ')
fi
python chunk.py $CORES $1 $2 $3 $4 $5
