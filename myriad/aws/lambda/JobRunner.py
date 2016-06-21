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
    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    found = 0
    result = Job()
    jobGUID = ""
    logger.info(event['source_ip'])
    
    try:
        with conn.cursor() as cur:
            sql = "SELECT Jobs.JobID, Jobs.JobName, Jobs.JobDefinition, Jobs.Created, Jobs.MakeInputDatParameters, Jobs.JobGroup FROM Jobs LEFT JOIN Executions ON Jobs.JobID = Executions.JobID WHERE Jobs.JobID NOT IN (SELECT DISTINCT JobID FROM JobResults)GROUP BY Jobs.JobID ORDER BY COUNT(Executions.JobID), Jobs.JobID  ASC LIMIT 1"
            cur.execute(sql)
            for row in cur:
                found = 1
                result.id = row[0]
                result.name = row[1]
                result.jobDefinition = row[2]
                result.created = row[3]
                result.makeInputDatParameters = row[4]
                result.jobGroup = row[5]
                #print(row)
                
            if 'source_ip' in event and event['source_ip'] != "" and found == 1:
                machineID = event['source_ip']
                logger.info("Adding record to Executions table")
                with conn.cursor() as cur:
                    sql = "INSERT INTO Executions (JobId, JobStarted, MachineID, JobGUID) VALUES (%s, NOW(), %s, UUID())"
                    cur.execute(sql, (str(result.id), machineID))
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
            return '# JobID: ' + str(result.id) + '\n# MakeInputDatParameters: ' + str(result.makeInputDatParameters) + '\n# JobGroup: ' + str(result.jobGroup) + '\n' + result.jobDefinition
        else:
            return '# JobID: ' + str(result.id) + '\n# MakeInputDatParameters: ' + str(result.makeInputDatParameters) + '\n# JobGroup: ' + str(result.jobGroup) + '\n# JobGUID: ' + str(jobGUID) + result.jobDefinition
    else:
        raise Exception('404: No jobs found')
