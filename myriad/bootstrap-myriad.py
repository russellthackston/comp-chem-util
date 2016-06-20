import requests
import importlib
import libmyriad
import myriad
import time

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

        def run(self):
                result = libmyriad.ResultCode.success
                while(True):

                        # run a myriad job
                        m = myriad.Myriad()
                        result = m.runOnce()

                        if result == libmyriad.ResultCode.success:
                                print('Job completed. Checking for another job.')
                        elif result == libmyriad.ResultCode.failure:
                                print('Job failed. Checking for another job.')
                        elif result == libmyriad.ResultCode.noaction:
                                print('No jobs found. Retrying in 60 seconds...')
                                time.sleep(60)

                        # Download a (potentially) updated copy of Myriad
                        self.downloadMyriad()

                        # Remove this after testing
                        break

b = Bootstrap()
b.run()
