import requests
import importlib

class Bootstrap:

        server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'

        def downloadMyriad(self, reload):
                self.downloadMyriadFile('libmyriad.py')
                self.downloadMyriadFile('myriad.py')
                from libmyriad import ResultCode
                from myriad import Myriad
                if reload:
                        importlib.reload(libmyriad)
                        importlib.reload(myriad)

        def downloadMyriadFile(self, filename):
                r = requests.get(self.server + filename)
                f = open(filename, 'w')
                f.write(r.text)
                f.flush()
                f.close()

        def run(self):
                # Initial import of myriad script from github
                self.downloadMyriad(False)

                while(True):

                        # run myriad (once)
                        m = myriad.Myriad()
                        result = m.runOnce()

                        # Reload myriad script, in case it changed on the server
                        self.downloadMyriad(True)
                        m.loadConfig()
                        break

b = Bootstrap()
b.run()
