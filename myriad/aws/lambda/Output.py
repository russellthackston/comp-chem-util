import sys
import logging
import rds_config
import pymysql
import jsonpickle
import datetime
from jobresult import JobResult

#rds settings
rds_host  = rds_config.db_host
username = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = rds_config.db_port

logger = logging.getLogger()
logger.setLevel(logging.INFO)

server_address = (rds_host, port)

def get(event, context):
    # Get the starting offset from the first record
    if 'start' not in event:
        start = 0
    else:
        start = int(event['start'])

    # Get the page size
    if 'pagesize' not in event:
        pagesize = 10
    else:
        pagesize = int(event['pagesize'])

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    found = 0
    result = []

    try:
        with conn.cursor() as cur:
            sql = "SELECT JobResultsID, JobID, OutputFile, ResultsCollected, MachineID, Filename, JobGUID FROM JobResults ORDER BY JobResultsID LIMIT %s, %s"
            cur.execute(sql, (start, pagesize))
            for row in cur:
                found = 1
                j = JobResult()
                j.id = row[0]
                j.jobID = row[1]
                j.outputFile = row[2]
                j.collected = row[3].isoformat()
                j.machineID = row[4]
                j.filename = row[5]
                j.jobGUID = row[6]
                result.append(j)

    finally:
        conn.close()

    if found == 1:
        return jsonpickle.encode(result, unpicklable=False)
    else:
        raise Exception('404: No job results found')

def post(event, context):
    # Get Job GUID
    if 'jobGUID' not in event:
        raise Exception('400: Missing job GUID')
    jobGUID = event['jobGUID']
    if jobGUID == '':
        raise Exception('400: Missing job GUID')

    # Get filename
    if 'filename' not in event:
        raise Exception('400: Missing filename')
    filename = event['filename']
    if filename == '':
        raise Exception('400: Missing filename')

    # Get the output file contents
    if 'outputFile' not in event:
        raise Exception('400: Missing output file contents')
    outputFile = event['outputFile']
    if outputFile == '':
        raise Exception('400: Missing output file contents')

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    try:
        with conn.cursor() as cur:
            sql = "SELECT JobID, MachineID FROM Executions WHERE JobGUID = %s"
            cur.execute(sql, jobGUID)
            for row in cur:
                found = 1
                jobID = row[0]
                machineID = row[1]
            
            sql = "INSERT INTO JobResults (JobID, OutputFile, MachineID, Filename, JobGUID, ResultsCollected) VALUES (%s, %s, %s, %s, %s, NOW())"
            cur.execute(sql, (jobID, outputFile, machineID, filename, jobGUID))
            conn.commit()
            resultID = cur.lastrowid
            logger.info("Added JobResults ID of " + str(resultID))

    finally:
        conn.close()


