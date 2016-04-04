import sys
import logging
import rds_config
import pymysql
import jsonpickle
import datetime
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
    id = None
    name = None
    start = None
    pagesize = None
    
    # Get the requested job id
    if 'id' not in event:
        logger.info("ID not provided")
    else:
        id = event['id']
        if id == "":
            id = None

    # Get the requested job name
    if 'name' not in event:
        logger.info("Job name not provided")
    else:
        name = event['name']
        if name == "":
            name = None

    # Get the starting offset from the first record
    if 'start' not in event:
        logger.info("Start not provided")
        start = 0
    else:
        start = event['start']
        if start == "":
            start = 0

    # Get the page size
    if 'pagesize' not in event:
        logger.info("Pagesize not provided")
        pagesize = 10
    else:
        pagesize = event['pagesize']
        if pagesize == "":
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
            if id is not None:
                sql = "SELECT JobID, JobName, InputFile, Created FROM Jobs WHERE JobID = %s"
                cur.execute(sql, (id))
            elif name is not None:
                sql = "SELECT JobID, JobName, InputFile, Created FROM Jobs WHERE JobName = %s"
                cur.execute(sql, (name))
            else:
                sql = "SELECT JobID, JobName, InputFile, Created FROM Jobs ORDER BY JobID LIMIT %s, %s"
                cur.execute(sql, (int(start), int(pagesize)))
            for row in cur:
                found = 1
                j = Job()
                j.id = row[0]
                j.name = row[1]
                j.inputFile = row[2]
                if row[3] is not None:
                    j.created = row[3].isoformat()
                else:
                    j.created = ""
                result.append(j)

    finally:
        conn.close()

    if found == 1:
        if id is not None or name is not None:
            return jsonpickle.encode(j, unpicklable=False)
        else:
            return jsonpickle.encode(result, unpicklable=False)
    else:
        raise Exception('404: No job(s) found')

def post(event, context):
    # Get job name
    if 'jobname' not in event:
        raise Exception('400: Missing job name')
    jobname = event['jobname']
    if jobname == '':
        raise Exception('400: Missing job name')

    # Get the input file contents
    if 'inputFile' not in event:
        raise Exception('400: Missing input file contents')
    inputFile = event['inputFile']
    if inputFile == '':
        raise Exception('400: Missing input file contents')

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    try:
        with conn.cursor() as cur:
            sql = "SELECT COUNT(*) FROM Jobs WHERE JobName = %s"
            cur.execute(sql, jobname)
            for row in cur:
                if int(row[0]) > 0:
                    raise Exception('400: Job name already exists')

            sql = "INSERT INTO Jobs (JobName, InputFile, Created) VALUES (%s, %s, NOW())"
            cur.execute(sql, (jobname, inputFile))
            conn.commit()
            resultID = cur.lastrowid
            logger.info("Added JobResults ID of " + str(resultID))
            result = Job()
            result.id = resultID
            result.name = jobname
            result.inputFile = inputFile
            result.created = datetime.datetime.now().isoformat()

    finally:
        conn.close()

    return jsonpickle.encode(result, unpicklable=False)

