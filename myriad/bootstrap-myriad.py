import requests
import importlib
import libmyriad
import myriad
import time
import sys

class Bootstrap:

        server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'

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

                        if os.path.isfile('myriad.halt'):
                                return
                        while os.path.isfile('myriad.pause'):
                                time.sleep(5)

                        # Download a (potentially) updated copy of Myriad
                        self.downloadMyriad()

jobGroup=None
if len(sys.argv) > 1:
        jobGroup=sys.argv[1]
b = Bootstrap()
b.run(jobGroup)
