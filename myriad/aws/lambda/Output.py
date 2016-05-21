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

def post(event, context):
    # Get Job GUID
    if 'jobGUID' not in event:
        raise Exception('400: Missing job GUID')
    jobGUID = event['jobGUID']
    if jobGUID == '':
        raise Exception('400: Missing job GUID')

    # Get the output file contents
    if 'jobResults' not in event:
        raise Exception('400: Missing job results')
    jobResults = event['jobResults']
    if jobResults == '':
        raise Exception('400: Missing job results')

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")
    logger.info(event)

    try:
        with conn.cursor() as cur:
            sql = "SELECT JobID, MachineID FROM Executions WHERE JobGUID = %s"
            cur.execute(sql, jobGUID)
            for row in cur:
                found = 1
                jobID = row[0]
                sourceIP = row[1]
            
            if found == 1:
                    sql = "INSERT INTO JobResults (JobID, JobResults, MachineID, JobGUID, ResultsCollected) VALUES (%s, %s, %s, %s, NOW())"
                    cur.execute(sql, (jobID, jobResults, str(event['source_ip']), jobGUID))
                    conn.commit()
                    resultID = cur.lastrowid
                    logger.info("Added JobResults ID of " + str(resultID))

    finally:
        conn.close()


