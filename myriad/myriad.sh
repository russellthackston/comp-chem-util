function uploadFiles() {
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
}

function startJob() {
        rm -Rf $SCRATCH/* 2> /dev/null

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

	popd

        if [ "$RESP_CODE" != "200" ]; then
                echo No more jobs found in job set
                rm -Rf $DIR_NAME
        fi
}

# Check for command line parameters
USAGE="USAGE: myriad.sh -u BASE_URL -m MACHINE_NAME (-b BENCHMARK_JOBSET_NUMBER | -j JOBSET_NUMBER) [-h] [-l]\nThe -l flag only uploads existing files in the current folder. No jobs are run."
SHOW_USAGE="false"
BASE_URL="unknown"
MACHINE_NAME="unknown"
BENCHMARK_JOBSET_NUMBER="unknown"
JOBSET_NUMBER="unknown"
JOB_TYPE="unknown"
UPLOAD_FILES="unknown"
UPLOAD_FROM="unknown"
ETH_ADAPTER_NAME="eth0"

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
		-e)
		ETH_ADAPTER_NAME="$2"
		shift
		;;
		-h)
		SHOW_USAGE="true"
		;;
		-l)
		UPLOAD_FILES="true"
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

if [[ "$UPLOAD_FILES" == "true" ]]; then
        uploadFiles
        exit 0
fi

# http://myriad.elasticbeanstalk.com/api
SCRATCH=/tmp

# Get the MAC address and store in a file for later
MAC_ADDRESS="$(ifconfig "${ETH_ADAPTER_NAME}" | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')"
if [[ "$MAC_ADDRESS" == "" ]]; then
	echo "Could not get a MAC address. Try adding the -e (adapter name) flag to the command."
	exit 1
fi

# Replace colons in MAC address and write to file
MAC_ADDRESS=${MAC_ADDRESS//:/-}
echo $MAC_ADDRESS > mac.txt
echo MAC address determined to be $MAC_ADDRESS

# Build the URL to request a new/existing machine ID
POST_REQUEST="${BASE_URL}"'/machines/'"${MAC_ADDRESS}"'?name='"${MACHINE_NAME}"
echo Accessing web service: $POST_REQUEST

# Call the web service and store the response value
MAC_ID=$(curl --request POST ${POST_REQUEST} -d "")
echo $MAC_ID > id.txt
echo Your machine ID is $MAC_ID

startJob

while [ "$RESP_CODE" = "200" ]; do

	# Get the job number from the input.dat file
	JOB_NUMBER=$(head -n 1 input.dat | cut -d':' -f 2)
	JOB_NUMBER="$(echo -e "${JOB_NUMBER}" | tr -d '[[:space:]]')"
	echo Identified job number as $JOB_NUMBER

	if [[ $OSTYPE == *"linux"* ]]; then
		CORES=$(lscpu|grep 'CPU(s)'|head -n 1|tr -s ' '|cut -f 2 -d ' ')
	else
		CORES=$(sysctl hw.ncpu | cut -f 2 -d ' ')
	fi
	echo $CORES > cpu.txt

	# Check the free memory
	if [[ $OSTYPE == *"linux"* ]]; then
		FREE_MEM=$(free -m | grep Mem: | tr -s ' ' | cut -f 4 -d ' ')
	else
		FREE_MEM=$(top -l 1 -s 0 | grep 'PhysMem' | cut -f 6 -d ' ')
	fi
	FREE_MEM=$(echo $FREE_MEM|tr -d [A-Z][a-z])
	FREE_MEM=$[FREE_MEM/CORES]
	echo $FREE_MEM > freemem.txt
	sed -i -e "s/memory .*/memory ${FREE_MEM} MB/" input.dat

	echo Setting up to run PSI4 job...
	if [[ $OSTYPE == *"linux"* ]]; then
		export OMP_NUM_THREADS=$CORES
                export MKL_NUM_THREADS=$CORES
	else
		setenv OMP_NUM_THREADS $CORES
                setenv MKL_NUM_THREADS $CORES
	fi
	echo Set cores to $CORES with $FREE_MEM MB per core

	echo Running PSI4 job...
	if [[ $OSTYPE == *"linux"* ]]; then
		/usr/bin/time -v -o "time.out" psi4 > psi4.out 2> psi4.err
	else
		/usr/bin/time psi4 > psi4.out 2> psi4.err
	fi
	echo Done running PSI4 job.

	# Record the current disk usage
	echo Recording the current disk space and disk usage
	df -h > disk.txt
	ls -alh $SCRATCH >> scratch.txt

	uploadFiles

	# Clear the scratch space
	echo clearing the scratch folder
	rm -Rf $SCRATCH/* 2> /dev/null

	startJob

done


