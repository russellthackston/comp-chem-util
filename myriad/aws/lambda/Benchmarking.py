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
    # Get job set ID
    if 'id' not in event:
        raise Exception('400: Missing job set ID')
    jobsetid = event['id']
    if jobsetid == '':
        raise Exception('400: Missing job set ID')

    # Get machineID
    if 'machineID' not in event:
        raise Exception('400: Missing machine ID')
    machineID = event['machineID']
    if machineID == '':
        raise Exception('400: Missing machine ID')

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    found = 0
    result = Job()
    
    machineCount = 0
    executionID = -1

    try:
        with conn.cursor() as cur:
            sql = "SELECT Count(*) FROM Machines WHERE MachineID = %s"
            cur.execute(sql, str(machineID))
            for row in cur:
                machineCount = int(row[0])

            if machineCount > 0:
                with conn.cursor() as cur:
                    sql = "SELECT Jobs.JobID, Jobs.JobName, Jobs.InputFile, Jobs.Created FROM Jobs WHERE JobID IN (SELECT JobID FROM JobSetJobs, JobSets WHERE JobSetJobs.JobSetID = JobSets.JobSetID AND JobSets.JobSetID = %s ) AND JobID NOT IN (SELECT JobID FROM JobResults WHERE MachineID = %s) LIMIT 1"
                    cur.execute(sql, (str(jobsetid), str(machineID)))
                    for row in cur:
                        found = 1
                        result.id = row[0]
                        result.name = row[1]
                        result.inputFile = row[2]
                        result.created = row[3]
                        #print(row)

                if found == 1:
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
                        cur.execute(sql, str(executionID))
                        for row in cur:
                            jobGUID = row[0]
                        logger.info("JobGUID retrieved as " + str(jobGUID))

    finally:
        conn.close()

    #return { 'ID' : result.id, 'Name' : result.name, 'InputFile' : result.inputFile, 'Created' : result.created }
    if machineCount == 0:
        raise Exception('400: Machine ID not found')
    else:
        if found == 1:
            return '# JobID: ' + str(result.id) + '\n# JobGUID: ' + str(jobGUID) + '\n' + result.inputFile
        else:
            raise Exception('404: No jobs found')
