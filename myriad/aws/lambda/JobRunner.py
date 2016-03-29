import sys
import logging
import rds_config
import pymysql
from job import Job

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
    if 'id' not in event:
        raise Exception('400: Missing job set ID')
    jobsetid = event['id']
    if jobsetid == '':
        raise Exception('400: Missing job set ID')

    # Get machineID
    if 'machineID' in event:
        machineID = event['machineID']
    else:
        machineID = ""

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    found = 0
    result = Job()
    jobGUID = ""
    
    try:
        with conn.cursor() as cur:
            sql = "SELECT Jobs.JobID, Jobs.JobName, Jobs.InputFile, Jobs.Created FROM Jobs LEFT JOIN Executions ON Jobs.JobID = Executions.JobID WHERE Jobs.JobID IN (SELECT JobID FROM JobSetJobs, JobSets WHERE JobSetJobs.JobSetID = JobSets.JobSetID AND JobSets.JobSetID = %s) AND Jobs.JobID NOT IN (SELECT DISTINCT JobID FROM JobResults) GROUP BY Executions.JobID ORDER BY COUNT(Executions.JobID) ASC LIMIT 1"
            cur.execute(sql, str(jobsetid))
            for row in cur:
                found = 1
                result.id = row[0]
                result.name = row[1]
                result.inputFile = row[2]
                result.created = row[3]
                #print(row)
                
            if machineID != "":
                logger.info("Adding record to Executions table")
                with conn.cursor() as cur:
                    sql = "INSERT INTO Executions (JobId, JobStarted, MachineID, JobGUID) VALUES (%s, NOW(), %s, UUID())"
                    cur.execute(sql, (str(result.id), str(machineID)))
                    executionID = cur.lastrowid
                    conn.commit()
                    logger.info("Executions record added")

                    # Get the Job GUID
                    jobGUID = ""
                    sql = "SELECT JobGUID FROM Executions WHERE ExecutionID = %s"
                    cur.execute(sql, executionID)
                    for row in cur:
                        jobGUID = row[0]
                    logger.info("JobGUID retrieved as " + str(jobGUID))

    finally:
        conn.close()

    #return { 'ID' : result.id, 'Name' : result.name, 'InputFile' : result.inputFile, 'Created' : result.created }
    if found == 1:
        # Include the Job GUID, if we have one
        if jobGUID == "":
            return '# JobID: ' + str(result.id) + '\n' + result.inputFile
        else:
            return '# JobID: ' + str(result.id) + '\n# JobGUID: ' + str(jobGUID) + '\n' + result.inputFile
    else:
        raise Exception('404: No jobs found')
