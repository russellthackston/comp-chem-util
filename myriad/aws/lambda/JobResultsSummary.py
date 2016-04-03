import sys
import logging
import rds_config
import pymysql
import jsonpickle
import datetime
from jobresultsummary import JobResultsSummary

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
        start = event['start']
        if start = "":
        	start = 0

    # Get the page size
    if 'pagesize' not in event:
        pagesize = 10
    else:
        pagesize = event['pagesize']
        if pagesize = "":
        	pagesize = 10

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
            sql = "SELECT JobGUID, Success, ExecutionDateTime, Scratch, Memory, Memory2, UserTime, SystemTime, TotalTime, UserTime2, SystemTime2, WallClockTime, CPUpercent, ExitStatus, CPUs, FreeMem FROM psi4.JobResultsSummary ORDER BY ExecutionDateTime LIMIT %s, %s"
            cur.execute(sql, (int(start), int(pagesize)))
            for row in cur:
                found = 1
                j = JobResultsSummary()
                j.jobGUID = row[0]
                j.success = row[1]
                if row[2] is not None:
                    j.executionDateTime = row[2].isoformat()
                else:
                	j.executionDateTime = ""
                j.scratch = row[3]
                j.memory = row[4]
                j.memory2 = row[5]
                j.userTime = row[6]
                j.systemTime = row[7]
                j.totalTime = row[8]
                j.userTime2 = row[9]
                j.systemTime2 = row[10]
                j.wallClockTime = row[11]
                j.cpuPercent = row[12]
                j.exitStatus = row[13]
                j.cpus = row[14]
                j.freeMem=row[15]
                result.append(j)

    finally:
        conn.close()

    if found == 1:
        return jsonpickle.encode(result, unpicklable=False)
    else:
        raise Exception('404: No job summary found')

