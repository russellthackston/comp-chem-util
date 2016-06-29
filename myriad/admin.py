import pymysql
import rds_config
import argparse

rds_host  = rds_config.db_host
username = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = rds_config.db_port
server_address = (rds_host, port)

class AdminUtils:

        def addJobs(self, displacements, parameters, group):
                
                print("Adding jobs")

                try:
                        print("Connecting to database...")
                        conn = pymysql.connect(rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
                        print("Connected.")
                except:
                        logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
                        sys.exit()

                print("SUCCESS: Connection to RDS mysql instance succeeded")

                i = 1
                try:
                        for disp in displacements:
                                with conn.cursor() as cur:
                                        jobname = group + "-" + str(i)
                                        sql = "INSERT INTO Jobs (JobName, JobDefinition, Created, MakeInputDatParameters, JobGroup) VALUES (%s,%s,NOW(),%s,%s)"
                                        cur.execute(sql, (jobname, disp.strip(), parameters, group))
                                        jobID = cur.lastrowid
                                        conn.commit()
                                        print("Job record added for " + disp.strip() + " with jobID of " + str(jobID))
                                        i+=1
                finally:
                        conn.close()

        def usage(self):
                print("Use the 'add' operation to add job records to the Maestro database.")

parser = argparse.ArgumentParser(description='Admin tools for Maestro. Use --options for usage information')
parser.add_argument("operation", help="", type=str)
parser.add_argument("--usage", help="", action="store_true")
parser.add_argument("--displacements", help="Filename of a displacements file.", type=str)
parser.add_argument("--parameters", help="Parameters to be passed to jobConfig.py when generatin the input.dat file.", type=str)
parser.add_argument("--jobgroup", help="The name of this job group.", type=str)
args=parser.parse_args()


a = AdminUtils()
if args.usage:
        a.usage()
elif args.operation == "add":
        print("Add operation selected.")
        f = open(args.displacements)
        d = f.readlines()
        a.addJobs(d, args.parameters, args.jobgroup)
else:
        print("No operation specified.")



