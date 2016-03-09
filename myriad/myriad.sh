# Check for command line parameters
USAGE="USAGE: myriad.sh -u BASE_URL -m MACHINE_NAME (-b BENCHMARK_JOBSET_NUMBER | -j JOBSET_NUMBER) [-h]"
SHOW_USAGE="false"
BASE_URL="unknown"
MACHINE_NAME="unknown"
BENCHMARK_JOBSET_NUMBER="unknown"
JOBSET_NUMBER="unknown"
JOB_TYPE="unknown"

while [[ $# > 0 ]]
do
	key="$1"
	case $key in
		-u)
		BASE_URL="$2"
		shift
		;;
		-m)
		MACHINE_NAME="$2"
		shift
		;;
		-b)
		BENCHMARK_JOBSET_NUMBER="$2"
		JOB_TYPE="bench"
		shift
		;;
		-j)
		JOBSET_NUMBER="$2"
		JOB_TYPE="set"
		shift
		;;
		-h)
		SHOW_USAGE="true"
		;;
	esac
	shift
done

if [[ "$SHOW_USAGE" == "true" ]]; then
	echo $USAGE
	exit 0
fi

if [[ "$BASE_URL" == "unknown" ]]; then
        echo "Missing base url"
	echo $USAGE
        exit 1
fi

if [[ "$MACHINE_NAME" == "unknown" ]]; then
	echo "Missing machine name"
	echo $USAGE
	exit 1
fi

if [[ "$JOB_TYPE" == "unknown" ]]; then
        echo "Missing either job set number or benchmark set number"
	echo $USAGE
        exit 1
fi

# Write parameters to their respective files
if [[ "$BASE_URL" != "unknown" ]]; then
	echo $BASE_URL > url.txt
fi
if [[ "$MACHINE_NAME" != "unknown" ]]; then
	echo $MACHINE_NAME > name.txt
fi
if [[ "$BENCHMARK_JOBSET_NUMBER" != "unknown" ]]; then
	echo $BENCHMARK_JOBSET_NUMBER > bench.txt
fi
if [[ "$JOBSET_NUMBER" != "unknown" ]]; then
	echo $JOBSET_NUMBER > jobset.txt
fi

# http://myriad.elasticbeanstalk.com/api
SCRATCH=/tmp

function startJob() {
	sudo rm -Rf $SCRATCH/*

	# Make a folder for this job
	DIR_NAME=$(date +%Y%m%d_%H%M%S)
	mkdir $DIR_NAME
	pushd $DIR_NAME

	# Get the next job in the jobset
	echo Getting the next job in the jobset
	if [[ "$JOB_TYPE" == "bench" ]]; then
		INPUT_REQUEST="${BASE_URL}"'/benchmarking/'"${BENCHMARK_JOBSET_NUMBER}"'?machineID='"${MAC_ID}"
	fi
	if [[ "$JOB_TYPE" == "set" ]]; then
                INPUT_REQUEST="${BASE_URL}"'/jobrunner/'"${JOBSET_NUMBER}"'?machineID='"${MAC_ID}"
        fi

	echo Accessing web service: $INPUT_REQUEST
	curl --request GET ${INPUT_REQUEST} -w "\n\n# Response Code: %{http_code}\n" -d "" > input.dat
	echo Input.dat file written to $(pwd)

	RESP_CODE=$(tail -n 1 input.dat | cut -d':' -f 2)
	RESP_CODE="$(echo -e "${RESP_CODE}" | tr -d '[[:space:]]')"
	echo Identified response code as $RESP_CODE

	if [ "$RESP_CODE" != "200" ]; then
	        echo No more jobs found in job set
	        popd
	        rm -Rf $DIR_NAME
	fi
}

# Check for a previous URL
if [[ -f url.txt ]]; then
        BASE_URL=$(cat url.txt)
fi

# If the file contained a non-blank url, use it
if [[ "$BASE_URL" != "" ]]; then
        echo Url $BASE_URL read from url.txt
else
# If there was not a url in the file, get one from the user
        BASE_URL=Unknown
        nm1=foo
        nm2=bar
        while [ "$nm1" != "$nm2" ]
        do
                echo -n "Enter the url of the web service and press [ENTER]: "
                read nm1
                echo -n "Reenter the url of the web service and press [ENTER]: "
                read nm2
                if [ "$nm1" != "$nm2" ]; then
                        echo "Urls do not match"
                else
                        BASE_URL=$nm1
                fi
        done
        echo Url set to $BASE_URL
        echo $BASE_URL > url.txt
fi

# Check for a previous machine name
if [[ -f name.txt ]]; then
	MAC_NAME=$(cat name.txt)
fi

# If the file contained a non-blank name, use it
if [[ "$MAC_NAME" != "" ]]; then
	echo Machine name $MAC_NAME read from name.txt
else
# If there was not a name in the file, get one from the user
	MAC_NAME=Unknown
	nm1=foo
	nm2=bar
	while [ "$nm1" != "$nm2" ]
	do
	        echo -n "Enter this machine's name and press [ENTER]: "
        	read nm1
	        echo -n "Reenter this machine's name and press [ENTER]: "
        	read nm2
        	if [ "$nm1" != "$nm2" ]; then
                	echo "Names do not match"
        	else
                	MAC_NAME=$nm1
        	fi
	done
	echo Machine name set to $MAC_NAME
	echo $MAC_NAME > name.txt
fi

# Get the MAC address and store in a file for later
MAC_ADDRESS=$(ifconfig en0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')
if [ "$MAC_ADDRESS" = "" ]; then
	MAC_ADDRESS=$(ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')
fi

# Replace colons in MAC address and write to file
MAC_ADDRESS=${MAC_ADDRESS//:/-}
echo $MAC_ADDRESS > mac.txt
echo MAC address determined to be $MAC_ADDRESS

# Build the URL to request a new/existing machine ID
POST_REQUEST="${BASE_URL}"'/machines/'"${MAC_ADDRESS}"'?name='"${MAC_NAME}"
echo Accessing web service: $POST_REQUEST

# Call the web service and store the response value
MAC_ID=$(curl --request POST ${POST_REQUEST} -d "")
echo $MAC_ID > id.txt
echo Your machine ID is $MAC_ID

#If a jobset file exists, read its contents
BENCHMARK_JOBSET_NUMBER=""
if [[ -f bench.txt ]]; then
	BENCHMARK_JOBSET_NUMBER=$(cat bench.txt)
	if [ "$BENCHMARK_JOBSET_NUMBER" != "" ]; then
		JOB_TYPE="bench"
	fi
fi
if [[ -f jobset.txt ]]; then
        JOBSET_NUMBER=$(cat jobset.txt)
	if [ "$JOBSET_NUMBER" != "" ]; then
		JOB_TYPE="set"
	fi
fi

# If a jobset number was found in the file, use it
case "$JOB_TYPE" in
	bench)
	echo "Jobset number $BENCHMARK_JOBSET_NUMBER found in bench.txt"
        ;;
	set)
	echo "Jobset number $JOBSET_NUMBER found in jobset.txt"
	;;
	*)
	echo "Missing benchmarking or jobset number"
	exit 0
	;;
esac

startJob

while [ "$RESP_CODE" = "200" ]; do

	# Get the job number from the input.dat file
	JOB_NUMBER=$(head -n 1 input.dat | cut -d':' -f 2)
	JOB_NUMBER="$(echo -e "${JOB_NUMBER}" | tr -d '[[:space:]]')"
	echo Identified job number as $JOB_NUMBER

	if [[ "$OSTYPE" = "linux" || "$OSTYPE" = "linux-gnu" ]]; then
		CORES=$(lscpu|grep 'CPU(s)'|head -n 1|tr -s ' '|cut -f 2 -d ' ')
	else
		CORES=$(sysctl hw.ncpu | cut -f 2 -d ' ')
	fi
	echo $CORES > cpu.txt

	# Check the free memory
	if [[ "$OSTYPE" = "linux" || "$OSTYPE" = "linux-gnu" ]]; then
		FREE_MEM=$(free -m | grep Mem: | tr -s ' ' | cut -f 4 -d ' ')
	else
		FREE_MEM=$(top -l 1 -s 0 | grep 'PhysMem' | cut -f 6 -d ' ')
	fi
	FREE_MEM=$(echo $FREE_MEM|tr -d [A-Z][a-z])
	FREE_MEM=$[FREE_MEM/CORES]
	echo $FREE_MEM > freemem.txt
	sed -i -e "s/memory .*/memory ${FREE_MEM} MB/" input.dat

	echo Setting up to run PSI4 job...
	if [[ "$OSTYPE" = "linux" || "$OSTYPE" = "linux-gnu" ]]; then
		export OMP_NUM_THREADS=$CORES
                export MKL_NUM_THREADS=$CORES
	else
		setenv OMP_NUM_THREADS $CORES
                setenv MKL_NUM_THREADS $CORES
	fi
	echo Set cores to $CORES with $FREE_MEM MB per core

	echo Running PSI4 job...
	if [[ "$OSTYPE" = "linux" || "$OSTYPE" = "linux-gnu" ]]; then
		/usr/bin/time -v -o "time.out" psi4 > psi4.out 2> psi4.err
	else
		/usr/bin/time psi4 > psi4.out 2> psi4.err
	fi
	echo Done running PSI4 job.

	# Record the current disk usage
	echo Recording the current disk space and disk usage
	df -h > disk.txt
	ls -alh $SCRATCH >> disk.txt

	echo Uploading output files...
	UUID=$(uuidgen)
	echo Using common ID ${UUID}

	for f in *
	do
		OUTPUT_REQUEST="${BASE_URL}"'/output/'"${JOB_NUMBER}"'?machineID='"${MAC_ID}"'&filename='"${f}"'&uuid='"${UUID}"
		if [ -s $f ]; then
			echo Uploading $f
			echo Accessing web service: $OUTPUT_REQUEST
			curl --request POST ${OUTPUT_REQUEST} -H "Content-Type: text/plain" --data-binary "@${f}"
		else
			echo Skipping upload of empty file $f
		fi
	done

	# Clear the scratch space
	echo clearing the scratch folder
	sudo rm -Rf $SCRATCH/*

	popd

	startJob

done


