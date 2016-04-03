import sys
import logging
import rds_config
import pymysql
import jsonpickle
import datetime
from machine import Machine

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
    result = []

    try:
        with conn.cursor() as cur:
            sql = "SELECT MachineID, MAC, Created, Name FROM Machines"
            cur.execute(sql)
            for row in cur:
                found = 1
                m = Machine()
                m.id = row[0]
                m.mac = row[1]
                if row[2] is not None:
                    m.created = row[2].isoformat()
                else:
                    m.created = ""
                m.name = row[3]
                result.append(m)

    finally:
        conn.close()

    if found == 1:
        return jsonpickle.encode(result, unpicklable=False)
    else:
        raise Exception('404: No machines found')

def post(event, context):
    # Get MAC address
    if 'mac' not in event:
        raise Exception('400: Missing MAC address')
    mac = event['mac']
    if mac == '':
        raise Exception('400: Missing MAC address')

    # Get name
    if 'name' not in event:
        raise Exception('400: Missing machine name')
    name = event['name']
    if name == '':
        raise Exception('400: Missing machine name')

    try:
        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
    except:
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

    found = 0
    result = Machine()
    result.mac = mac
    result.name = name

    try:
        with conn.cursor() as cur:
            logger.info("Looking for machine...")
            sql = "SELECT MachineID, MAC, Created, Name FROM Machines WHERE MAC = %s AND Name = %s"
            cur.execute(sql, (mac, name))
            for row in cur:
                found = 1
                result.id = row[0]
                result.mac = row[1]
                if row[2] is not None:
                    result.created = row[2].isoformat()
                else:
                    result.created = ""
                result.name = row[3]
                logger.info("Found machine with ID " + str(result.id))
            
            # If the MAC/Name combination is not found in the database, add it
            if found == 0:
                logger.info("Machine not found. Creating...")
                sql = "INSERT INTO Machines (MAC, Created, Name) VALUES (%s, now(), %s)"
                cur.execute(sql, (mac, name))
                conn.commit()
                result.id = cur.lastrowid
                result.created = datetime.datetime.now().isoformat()

    finally:
        conn.close()

    return jsonpickle.encode(result, unpicklable=False)

