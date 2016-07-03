import sys
import logging
import rds_config
import pymysql
import json
import datetime


#rds settings
rds_host  = rds_config.db_host
username = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = rds_config.db_port

logger = logging.getLogger()
logger.setLevel(logging.INFO)

server_address = (rds_host, port)

class Job:
    
    def __init__(self, id="", name="", jobDefinition="", created="", makeInputDatParameters="", jobGroup=""):
        self.id = id
        self.name = name
        self.jobDefinition = jobDefinition
        self.created = created
        self.makeInputDatParameters = makeInputDatParameters
        self.jobGroup = jobGroup


'''
This function returns the next available job from the database, if one exists.
The job consists of some meta data (JobID, JobGroup, JobGUID, MakeInputDatParameters) and
the specific displacements values for that particular job: "0,0,0" or "2,2,0" etc.
This function is publicly available via API Gateway.
'''
def get_next_job(event, context):
        try:
                conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        except:
                logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
                sys.exit()

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        found = 0
        result = Job()
        jobGUID = ""
        machineID = event['source_ip']
        jobGroup = None
        if 'jobGroup' in event:
                if event['jobGroup'] != "":
                        jobGroup = event['jobGroup']
        
        try:
                with conn.cursor() as cur:
                        if jobGroup == None:
                                sql = "SELECT Jobs.JobID, Jobs.JobName, Jobs.JobDefinition, Jobs.Created, Jobs.MakeInputDatParameters, Jobs.JobGroup FROM Jobs WHERE Jobs.JobID NOT IN (SELECT DISTINCT JobID FROM Executions) LIMIT 1"
                                cur.execute(sql)
                        else:
                                sql = "SELECT Jobs.JobID, Jobs.JobName, Jobs.JobDefinition, Jobs.Created, Jobs.MakeInputDatParameters, Jobs.JobGroup FROM Jobs WHERE Jobs.JobID NOT IN (SELECT DISTINCT JobID FROM Executions) AND Jobs.JobGroup = %s LIMIT 1;"
                                cur.execute(sql, jobGroup)

                        found = False
                        for row in cur:
                                found = True
                                result.id = row[0]
                                result.name = row[1]
                                result.jobDefinition = row[2]
                                result.created = row[3]
                                result.makeInputDatParameters = row[4]
                                result.jobGroup = row[5]
                                
                        if found:
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
                        else:
                                logger.info("No jobs found")

        finally:
                conn.close()

        if found:
                return '# JobID: ' + str(result.id) + '\n# MakeInputDatParameters: ' + str(result.makeInputDatParameters) + '\n# JobGroup: ' + str(result.jobGroup) + '\n# JobGUID: ' + str(jobGUID) + "\n" + result.jobDefinition
        else:
                raise Exception('404: No jobs found')


'''
This function updates the database with the current job status and date/time.
Failed jobs can be manually deleted or otherwise addressed.
This function is not directly available to Myriad via the API Gateway.
It is invoked by the Maestro.dequeue_job_status_results() function.
'''
def post_job_status(event, context):
        try:
                conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        except:
                logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
                sys.exit()

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        machineID = str(event['source_ip'])[:15]
        jobGUID = str(event['jobGUID'])
        status = str(event['status'])
        lastUpdate = str(event['lastUpdate'])
        if 'message' in event:
                message = str(event['message'])[:255]
        else:
                message = None
        logger.info(machineID)
        logger.info(jobGUID)
        logger.info(status)
        logger.info(lastUpdate)
        updated = False
        
        if status.lower() == "success":
                stat = "0"
        else:
                stat = "1"
        logger.info("Setting status to '" + stat + "'")
        
        try:
                with conn.cursor() as cur:
                        sql = "UPDATE Executions SET ExecutionFailed = %s, LastUpdate = %s, LastStatusMessage = %s WHERE MachineID = %s AND JobGUID = %s"
                        cur.execute(sql, (stat, lastUpdate, machineID, message, jobGUID))
                        if cur.rowcount > 0:
                                updated = True
                        conn.commit()

        finally:
                conn.close()

        if updated:
                return "Execution record updated"
        else:
                raise Exception('404: Execution record not found')


'''
This function write a JobResults record to the database. Called by dequeue_job_results().
This function is not directly available to Myriad via the API Gateway.
It is invoked by the Maestro.dequeue_job_status_results() function.
'''
def post_job_results(event, context):
        # Get Job GUID
        if 'jobGUID' not in event:
                raise Exception('400: Missing job GUID')
        jobGUID = event['jobGUID']
        if jobGUID == '':
                raise Exception('400: Missing job GUID')

        # Get the calculation result
        if 'jobResults' not in event:
                raise Exception('400: Missing job results')
        jobResults = event['jobResults']
        if jobResults == '':
                raise Exception('400: Missing job results')

        # Get the source ip address
        if 'source_ip' not in event:
                raise Exception('400: Missing client IP address')
        source_ip = str(event['source_ip'])[:15]
        if source_ip == '':
                raise Exception('400: Missing client IP address')

        # Get the job completion date/time
        if 'completed' not in event:
                raise Exception('400: Missing completion date/time')
        completed = event['completed']
        if completed == '':
                raise Exception('400: Missing completion date/time')

        try:
                conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        except:
                logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
                sys.exit()

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")
        logger.info(event)

        try:
                with conn.cursor() as cur:
                        sql = "SELECT JobID FROM Executions WHERE JobGUID = %s AND MachineID = %s"
                        cur.execute(sql, (jobGUID, source_ip))
                        found = False
                        for row in cur:
                                found = True
                                jobID = row[0]

                        if found:
                                sql = "INSERT INTO JobResults (JobID, JobResults, MachineID, JobGUID, ResultsCollected) VALUES (%s, %s, %s, %s, %s)"
                                cur.execute(sql, (jobID, jobResults, source_ip, jobGUID, completed))
                                conn.commit()
                                resultID = cur.lastrowid
                                logger.info("Added JobResults ID of " + str(resultID))
                        else:
                                raise Exception('400: Job not found')

        finally:
                conn.close()
        
'''
This function returns a list of jobs from the database, from which may be derived the job
statuses. This function is directly available via the API Gateway.
'''
def get_jobs_details(event, context):
        try:
                conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        except:
                logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
                sys.exit()

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")
        logger.info(event)

        results = []
        try:
                with conn.cursor() as cur:
                        sql = '''
                                SELECT JobResultsID, MachineID, JobStatus, JobID, JobName, 
                                JobDefinition, Created, MakeInputDatParameters, JobGroup,
                                ExecutionID, JobStarted, ExecutionFailed, JobGUID, 
                                LastUpdate, JobResultsID, JobResults, ResultsCollected
                                FROM JobExecutionResultSummary
                                '''
                        cur.execute(sql)
                        found = False
                        for row in cur:
                                found = True
                                if row[6] != None:
                                        created = row[6].strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                        created = 'None'
                                if row[10] != None:
                                        jobStarted = row[10].strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                        jobStarted = 'None'
                                if row[13] != None:
                                        lastUpdate = row[13].strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                        lastUpdate = 'None'
                                if row[16] != None:
                                        collected = row[16].strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                        collected = 'None'
                                drow = { 'JobResultsID': str(row[0]), 'MachineID': str(row[1]), 'JobStatus': str(row[2]), 'JobID': str(row[3]), 'JobName': str(row[4]), 'JobDefinition': str(row[5]), 'Created' : str(created), 'MakeInputDatParameters': str(row[7]), 'JobGroup': str(row[8]), 'ExecutionID': str(row[9]), 'JobStarted': str(jobStarted), 'ExecutionFailed': str(row[11]), 'JobGUID': str(row[12]), 'LastUpdate': str(lastUpdate), 'JobResultsID': str(row[14]), 'JobResults': str(row[15]), 'ResultsCollected': str(collected) }
                                results.append(drow)
        finally:
                conn.close()

        return results
