function loadConfig() {
	echo "Loading web service endpoints..."

	WK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	echo "Getting values from config.txt in:"
	pushd $WK_DIR

	Benchmarking_GET="$(cat config.txt | grep Benchmarking_GET | cut -d ' ' -f 2)"
	JobRunner_GET="$(cat config.txt | grep JobRunner_GET | cut -d ' ' -f 2)"
	Machines_GET="$(cat config.txt | grep Machines_GET | cut -d ' ' -f 2)"
	Machines_POST="$(cat config.txt | grep Machines_POST | cut -d ' ' -f 2)"
	Output_GET="$(cat config.txt | grep Output_GET | cut -d ' ' -f 2)"
	Output_POST="$(cat config.txt | grep Output_POST | cut -d ' ' -f 2)"
	JobResultsSummary_GET="$(cat config.txt | grep JobResultsSummary_GET | cut -d ' ' -f 2)"
	Jobs_DELETE="$(cat config.txt | grep Jobs_DELETE | cut -d ' ' -f 2)"
	Jobs_GET="$(cat config.txt | grep Jobs_GET | cut -d ' ' -f 2)"
	Jobs_GET="$(cat config.txt | grep Jobs_GET | cut -d ' ' -f 2)"
	Jobs_GET="$(cat config.txt | grep Jobs_GET | cut -d ' ' -f 2)"
	Jobs_POST="$(cat config.txt | grep Jobs_POST | cut -d ' ' -f 2)"
	Jobs_PUT="$(cat config.txt | grep Jobs_PUT | cut -d ' ' -f 2)"
	JobSetJobs_DELETE="$(cat config.txt | grep JobSetJobs_DELETE | cut -d ' ' -f 2)"
	JobSetJobs_GET="$(cat config.txt | grep JobSetJobs_GET | cut -d ' ' -f 2)"
	JobSetJobs_PUT="$(cat config.txt | grep JobSetJobs_PUT | cut -d ' ' -f 2)"
	JobSets_DELETE="$(cat config.txt | grep JobSets_DELETE | cut -d ' ' -f 2)"
	JobSets_GET="$(cat config.txt | grep JobSets_GET | cut -d ' ' -f 2)"
	JobSets_GET="$(cat config.txt | grep JobSets_GET | cut -d ' ' -f 2)"
	JobSets_GET="$(cat config.txt | grep JobSets_GET | cut -d ' ' -f 2)"
	JobSets_POST="$(cat config.txt | grep JobSets_POST | cut -d ' ' -f 2)"
	JobSets_PUT="$(cat config.txt | grep JobSets_PUT | cut -d ' ' -f 2)"

	popd > /dev/null 2>&1
}

function uploadFiles() {
        echo Uploading output files...

        for f in *
        do
		# Substitute values for variables in URL
		OUTPUT_REQUEST="${Output_POST/\{jobGUID\}/$jobGUID}"
		OUTPUT_REQUEST="${OUTPUT_REQUEST/\{filename\}/$f}"
		OUTPUT_REQUEST="$(sed -e 's/[[:space:]]*$//' <<<${OUTPUT_REQUEST})"
                if [ -s $f ]; then
                        echo Uploading $f
                        echo Accessing web service: $OUTPUT_REQUEST
                        curl --request POST ${OUTPUT_REQUEST} -H "Content-Type: text/plain" --data-binary "@${f}" > /dev/null 2>&1
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
		# Substitute values for variables in URL
                INPUT_REQUEST="${Benchmarking_GET/\{id\}/$BENCHMARK_JOBSET_NUMBER}"
                INPUT_REQUEST="${INPUT_REQUEST/\{machineID\}/$MAC_ID}"
        fi
        if [[ "$JOB_TYPE" == "set" ]]; then
		# Substitute values for variables in URL
                INPUT_REQUEST="${JobRunner_GET/\{id\}/$JOBSET_NUMBER}"
                INPUT_REQUEST="${INPUT_REQUEST/\{machineID\}/$MAC_ID}"
        fi
	INPUT_REQUEST="$(sed -e 's/[[:space:]]*$//' <<<${INPUT_REQUEST})"

        echo Accessing web service: $INPUT_REQUEST
        curl --request GET ${INPUT_REQUEST} -w "\n\n# Response Code: %{http_code}\n" -H "Content-Type: text/plain" -d "" > input.dat
        echo Input.dat file written to $(pwd)

        RESP_CODE=$(tail -n 1 input.dat | cut -d':' -f 2)
        RESP_CODE="$(echo -e "${RESP_CODE}" | tr -d '[[:space:]]')"
        echo Identified response code as $RESP_CODE

        if [ "$RESP_CODE" != "200" ]; then
                echo No more jobs found in job set
		popd
                rm -Rf $DIR_NAME
	else
		jobGUID=$(head -n 2 input.dat | tail -n 1 | cut -d ":" -f 2)
		# Remove whitespace
		jobGUID="$(sed -e 's/[[:space:]]*$//' <<<${jobGUID})"
		echo $jobGUID
        	# JobGUID: 0c301a96-f877-11e5-b694-069f340cc9ab
        fi
}

# Check for command line parameters
USAGE="USAGE: myriad.sh -m MACHINE_NAME (-b BENCHMARK_JOBSET_NUMBER | -j JOBSET_NUMBER) [-h] [-l]"
SHOW_USAGE="false"
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

loadConfig

if [[ "$UPLOAD_FILES" == "true" ]]; then
        uploadFiles
        exit 0
fi

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
POST_REQUEST="${Machines_POST/\{mac\}/$MAC_ADDRESS}"
POST_REQUEST="${POST_REQUEST/\{name\}/$MACHINE_NAME}"
POST_REQUEST="$(sed -e 's/[[:space:]]*$//' <<<${POST_REQUEST})"
echo Accessing web service: $POST_REQUEST

# Call the web service and store the response value
curl --request POST ${POST_REQUEST} -w "\n\n# Response Code: %{http_code}\n" -H "Content-Type: text/plain" -d "" > id.txt
MAC_ID=$(head -n 1 id.txt)
RESP_CODE=$(tail -n 1 id.txt | cut -d ':' -f 2)
# Remove whitespace
RESP_CODE="$(sed -e 's/[[:space:]]*$//' <<<${RESP_CODE})"
if [ "$RESP_CODE" = "200" ]; then
	MAC_ID=$(head -n 1 id.txt | cut -d "," -f 2 | cut -d ":" -f 2)
	# Remove whitespace
	MAC_ID="$(sed -e 's/[[:space:]]*$//' <<<${MAC_ID})"
	echo Your machine ID is $MAC_ID
else
	echo "Error obtaining machine ID"
	exit 1
fi

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
	export OMP_NUM_THREADS=$CORES
        export MKL_NUM_THREADS=$CORES
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

	popd

	startJob

done


