function loadConfig() {
	echo "Loading web service endpoints..."

	WK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	echo "Getting values from config.txt in:"
	pushd $WK_DIR

	JobRunner_GET="$(cat config.txt | grep JobRunner_GET | cut -d ' ' -f 2)"
	Output_POST="$(cat config.txt | grep Output_POST | cut -d ' ' -f 2)"

	popd > /dev/null 2>&1
}

function uploadResults() {
	RETRIES=0
	UPRESP_CODE="0"
	while [ "$UPRESP_CODE" != "200" ] && [ $RETRIES -lt 3 ]; do
	        echo Attempting to upload results...

		# Substitute values for variables in URL
        	OUTPUT_REQUEST="${Output_POST}?jobGUID=${jobGUID}"
        	OUTPUT_REQUEST="$(sed -e 's/[[:space:]]*$//' <<<${OUTPUT_REQUEST})"

        	echo Accessing web service: $OUTPUT_REQUEST
        	curl --request POST ${OUTPUT_REQUEST} -w "# Response Code: %{http_code}\n" -H "Content-Type: text/plain" -d @result.dat > upload.dat
        	echo Upload results written to $(pwd) in upload.dat

        	UPRESP_CODE=$(tail -n 1 upload.dat | cut -d':' -f 2)
        	UPRESP_CODE="$(echo -e "${UPRESP_CODE}" | tr -d '[[:space:]]')"
        	echo Identified response code as $UPRESP_CODE

        	if [ "$UPRESP_CODE" != "200" ] && [ $RETRIES < 3 ]; then
                	echo Upload error. Retrying in 30 seconds...
			let RETRIES=RETRIES+1
			sleep 30
		else
			if [ $RETRIES -eq 3 ]; then
				echo Quitting after three failed attempts
				break
			fi
        	fi
	done
}

function startJob() {
        rm -Rf $SCRATCH/* 2> /dev/null

        # Make a folder for this job
        DIR_NAME=$(date +%Y%m%d_%H%M%S)
	echo Creating folder $DIR_NAME
        mkdir $DIR_NAME
        pushd $DIR_NAME

        # Get the next job in the jobset
        echo Getting the next job in the jobset

	# Substitute values for variables in URL
	INPUT_REQUEST="${JobRunner_GET}"
	INPUT_REQUEST="$(sed -e 's/[[:space:]]*$//' <<<${INPUT_REQUEST})"

        echo Accessing web service: $INPUT_REQUEST
        curl --request GET ${INPUT_REQUEST} -w "\n\n# Response Code: %{http_code}\n" -H "Content-Type: text/plain" -d "" > disp.dat
        echo Displacements file written to $(pwd)

        RESP_CODE=$(tail -n 1 disp.dat | cut -d':' -f 2)
        RESP_CODE="$(echo -e "${RESP_CODE}" | tr -d '[[:space:]]')"
        echo Identified response code as $RESP_CODE

        if [ "$RESP_CODE" != "200" ]; then
                echo "No job(s) found"
		popd
                rm -Rf $DIR_NAME
		sleep 60
	else

		# Copy the mk_input_dat.* script to the job folder
		cp ../mk_input_dat.* .

		# Build an input.dat file from the displacements
		if [[ -f "mk_input_dat.sh" ]]; then
			chmod +x mk_input_dat.sh
			mk_input_dat.sh
		fi
		if [[ -f "mk_input_dat.py" ]]; then
                        python mk_input_dat.py
                fi
		if [[ ! -f "input.dat" ]]; then
			echo "Error: No input.dat found"
			exit 1
		fi
		echo -e "\nprint_variables()\n" >> input.dat

		# Get the job GUID from the disp.dat file
		jobGUID=$(head -n 2 disp.dat | tail -n 1 | cut -d ":" -f 2)
		# Remove whitespace
		jobGUID="$(sed -e 's/[[:space:]]*$//' <<<${jobGUID})"
		echo $jobGUID

		# Get the job number from the disp.dat file
        	JOB_NUMBER=$(head -n 1 disp.dat | cut -d':' -f 2)
        	JOB_NUMBER="$(echo -e "${JOB_NUMBER}" | tr -d '[[:space:]]')"
        	echo Identified job number as $JOB_NUMBER
        fi
}

loadConfig

SCRATCH=/tmp

startJob

while true; do

	if [ "$RESP_CODE" = "200" ]; then

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

		# Extact the results from the output.dat file
		ENERGYLINE=$(grep "CURRENT ENERGY" output.dat | tail -n 1)
		ENERGYVAL=${ENERGYLINE##*>}
		echo "$ENERGYVAL" > result.dat

		uploadResults

		# Clear the scratch space
		echo Clearing the scratch folder
		rm -Rf $SCRATCH/* 2> /dev/null

		popd
	fi

	startJob

done


