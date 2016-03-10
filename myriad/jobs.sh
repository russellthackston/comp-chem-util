# Check for command line parameters
USAGE="USAGE: jobs.sh -u BASE_URL -k ADMIN_KEY [-f INPUT_FILE] [-h]"
SHOW_USAGE="false"
BASE_URL="unknown"
ADMIN_KEY="unknown"
INPUT_FILE="input.dat"

while [[ $# > 0 ]]
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
                INPUT_FILE="$2"
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

if [[ "$ADMIN_KEY" == "unknown" ]]; then
        echo "Missing admin key"
        echo $USAGE
        exit 1
fi

OUTPUT_REQUEST="${BASE_URL}"'/jobs'
if [ -s $INPUT_FILE ]; then
	echo Uploading $INPUT_FILE
        echo Accessing web service: $OUTPUT_REQUEST
               curl --request POST ${OUTPUT_REQUEST} -H "Content-Type: text/plain" -H "Authorization: ${ADMIN_KEY}" --data-binary "@${INPUT_FILE}"
else
        echo Skipping upload of empty file $INPUT_FILE
fi

