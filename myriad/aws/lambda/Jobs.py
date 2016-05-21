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
    start = None
    pagesize = None
    
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
                sql = "SELECT JobID, JobName, InputFile, Created FROM Jobs"
                cur.execute(sql, (id))
            elif name is not None:
                sql = "SELECT JobID, JobName, InputFile, Created FROM Jobs"
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

