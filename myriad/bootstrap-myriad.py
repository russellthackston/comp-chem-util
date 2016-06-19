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
                while(True):

                        # run myriad (once)
                        m = myriad.Myriad()
                        result = m.runOnce()

                        # Reload myriad script, in case it changed on the server
                        self.downloadMyriad()
                        break

b = Bootstrap()
b.run()
