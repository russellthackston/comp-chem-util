import requests
import importlib
import libmyriad
import myriad

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
                while(result != libmyriad.ResultCode.abort):

                        # run a myriad job
                        m = myriad.Myriad()
                        result = m.runOnce()

                        if result != libmyriad.ResultCode.success:
                                # Download a (potentially) updated copy of Myriad
                                self.downloadMyriad()

                        break

b = Bootstrap()
b.run()
