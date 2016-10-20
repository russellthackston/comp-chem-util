import argparse
import glob
import importlib
import libmyriad
import myriad
import os
import requests
import shutil
import subprocess
import sys
import time

class Bootstrap:

        server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'
        
        def __init__(self):
                pass

        def downloadMyriad(self):
                self.downloadMyriadFile('libmyriad.py')
                self.downloadMyriadFile('myriad.py')
                importlib.reload(libmyriad)
                importlib.reload(myriad)

        def downloadMyriadFile(self, filename):
                r = requests.get(self.server + filename)
                f = open(filename, 'w')
                f.write(r.text)
                f.flush()
                f.close()

        def run(self, jobGroup=None, jobCategory=None):
                print("Job group = " + str(jobGroup))
                print("Job category = " + str(jobCategory))
                result = libmyriad.ResultCode.success
                while(True):

                        # run a myriad job
                        m = myriad.Myriad()
                        result = m.runOnce(jobGroup, jobCategory)

                        # Upload job folder(s) to S3 and delete for local drive
                        if glob.glob("*.zip"):
                                command = "aws s3 cp *.zip s3://myriaddropbox/"
                                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                                command = "rm -Rf *.zip"
                                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

                        if result == libmyriad.ResultCode.success:
                                print('Job completed. Checking for another job.')
                        elif result == libmyriad.ResultCode.failure:
                                print('Job failed. Retrying in 10 seconds...')
                                time.sleep(10)
                        elif result == libmyriad.ResultCode.noaction:
                                # this file should be created by the start-up script or manually by the user
                                if os.path.isfile('shutdown.myriad'):
                                        print('No jobs found. Shutting down...')
                                        
                                        command = "/sbin/shutdown -h now"
                                        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                                print('No jobs found. Retrying in 60 seconds...')
                                time.sleep(60)

                        if os.path.isfile('die.myriad'):
                                return
                        while os.path.isfile('pause.myriad'):
                                time.sleep(5)

                        # Download a (potentially) updated copy of Myriad
                        self.downloadMyriad()

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--group', dest='group', action='store', type=str, help='Optional group for filtering the requested job')
parser.add_argument('--subGroup', dest='subGroup', action='store', type=str, help='Optional sub group for filtering the requested job')
args = parser.parse_args()

b = Bootstrap()
b.run(args.group, args.subGroup)
