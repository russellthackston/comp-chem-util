# Create a new project (job set) via web service
	# Remember the Jobset ID
# Create 1..n jobs via web service
	# Add each new job to the Jobset as you go

# Check for command line parameters
# Usage: newproj.sh -u BASE_URL (-k ADMIN_KEY | -f ADMIN_KEYFILE) -n PROJECT_NAME [-p PATH_TO_INPUT_FILES] [-m FILE_MASK]
BASE_URL="unknown"
ADMIN_KEY="unknown"
ADMIN_KEYFILE="unknown"
PATH_TO_INPUT_FILES="."
FILE_MASK="input.dat"
PROJECT_NAME="unknown"

function addToProject() {
        jobID="$1"
	projectID="$2"
        # Add the job to the project
        UPLOAD_REQUEST="${BASE_URL}/jobsetjobs/$projectID"
        echo Accessing web service: $UPLOAD_REQUEST
        RESP=$(curl --request PUT ${UPLOAD_REQUEST} -H "Content-Type: text/plain" -H "Authorization: $ADMIN_KEY" --data-binary "${jobID}" -w "\n%{http_code}")
        ARY=(${RESP//;/ })
        RESP_CODE=${ARY[0]}

        if [ "$RESP_CODE" != "200" ]; then
                echo "Error adding to project. Response code=$RESP_CODE"
                exit 2
        else
                echo "Job $jobID added to project $projectID"
        fi

        PROJECT_ID=$JOBSET_ID
}       

function createProject() {
        name="$1"
        # Push the project into the database
        UPLOAD_REQUEST="${BASE_URL}/jobsets/"
        echo Accessing web service: $UPLOAD_REQUEST
        RESP=$(curl --request POST ${UPLOAD_REQUEST} -H "Content-Type: text/plain" -H "Authorization: $ADMIN_KEY" --data-binary "${name}" -w "\n%{http_code}")
        ARY=(${RESP//;/ })
        JOBSET_ID=${ARY[0]}
        RESP_CODE=${ARY[1]}

        if [ "$RESP_CODE" != "200" ]; then
                echo "Error creating project. Response code=$RESP_CODE"
                exit 2
        else
                echo "Project created with ID: $JOBSET_ID"
        fi

	PROJECT_ID=$JOBSET_ID
}

function uploadJob() {
	g="$1"
	jobsetid="$2"
	# Push the job into the database
	UPLOAD_REQUEST="${BASE_URL}/jobs/"
	echo Accessing web service: $UPLOAD_REQUEST
	if [ -s $g ]; then
		echo Uploading $g
		echo Accessing web service: $UPLOAD_REQUEST
		RESP=$(curl --request POST ${UPLOAD_REQUEST} -H "Content-Type: text/plain" -H "Authorization: $ADMIN_KEY" --data-binary "@${g}" -w "\n%{http_code}")
		ARY=(${RESP//;/ })
		JOB_ID=${ARY[0]}
		RESP_CODE=${ARY[1]}
	else
		echo Skipping upload of empty file $g
	fi

	if [ "$RESP_CODE" != "200" ]; then
		if [ "$RESP_CODE" == "409" ]; then
                	echo "Error: Job name in file $g already exists in database."
		else
	        	echo "Error uploading job. Response code=$RESP_CODE"
		fi
	        exit 2
	else
		echo "Job uploaded with ID: $JOB_ID"
	fi
	
	# Add to jobset
	addToProject $JOB_ID $PROJECT_ID
}

while [[ $# > 1 ]]
do
	key="$1"
	case $key in
		-u)
		BASE_URL="$2"
		shift
		;;
		-k)
		ADMIN_KEY="$2"
		shift
		;;
		-f)
		ADMIN_KEYFILE="$2"
		shift
		;;
		-m)
		FILE_MASK="$2"
		shift
		;;
		-n)
		PROJECT_NAME="$2"
		shift
		;;
		-p)
                PATH_TO_INPUT_FILES="$2"
                shift
                ;;
	esac
	shift
done

if [[ "$BASE_URL" == "unknown" ]]; then
	echo "Error: Missing BASE_URL"
	exit 1
fi

if [[ "$PROJECT_NAME" == "unknown" ]]; then
	echo "Error: Missing PROJECT_NAME"
	exit 1
fi

# Check for the admin keyfile
if [[ "$ADMIN_KEYFILE" != "unknown" && -f "$ADMIN_KEYFILE" ]]; then
        ADMIN_KEY=$(cat $ADMIN_KEYFILE)
        echo "Admin key loaded from $ADMIN_KEYFILE"
fi

if [[ "$ADMIN_KEY" == "unknown" || "$ADMIN_KEY" == "" ]]; then
	echo "Error: Missing ADMIN_KEY $ADMIN_KEY"
	exit 1
fi

# Create the project (jobset)
createProject $PROJECT_NAME

OLD_IFS=$IFS
IFS=$'\n'
echo $FILE_MASK
for h in $(find $PATH_TO_INPUT_FILES -name "$FILE_MASK"); do 
	uploadJob $h $jobsetid
	echo $h
done
IFS=$OLD_IFS


