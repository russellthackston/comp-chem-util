import requests
import importlib
import libmyriad
import myriad
import time
import sys
import os

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

        def run(self, jobGroup=None):
                print("Job group = " + str(jobGroup))
                result = libmyriad.ResultCode.success
                while(True):

                        # run a myriad job
                        m = myriad.Myriad()
                        result = m.runOnce(jobGroup)

                        if result == libmyriad.ResultCode.success:
                                print('Job completed. Checking for another job.')
                        elif result == libmyriad.ResultCode.failure:
                                print('Job failed. Retrying in 10 seconds...')
                                time.sleep(10)
                        elif result == libmyriad.ResultCode.noaction:
                                print('No jobs found. Retrying in 60 seconds...')
                                time.sleep(60)

                        if os.path.isfile('die.myriad'):
                                return
                        while os.path.isfile('pause.myriad'):
                                time.sleep(5)

                        # Download a (potentially) updated copy of Myriad
                        self.downloadMyriad()

jobGroup=None
if len(sys.argv) > 1:
        print("Found job group parameter")
        jobGroup=sys.argv[1]
else:
        print("No job group parameter provided")
b = Bootstrap()
b.run(jobGroup)
