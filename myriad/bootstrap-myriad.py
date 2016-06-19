import requests
import importlib

m_server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'

def downloadMyriad(reload):
        downloadMyriadFile('libmyriad.py')
        downloadMyriadFile('myriad.py')
        from libmyriad import ResultCode
        from myriad import Myriad
        if reload:
                importlib.reload(libmyriad)
                importlib.reload(myriad)

def downloadMyriadFile(filename):
        r = requests.get(m_server + filename)
        f = open(filename, 'w')
        f.write(r.text)
        f.flush()
        f.close()

# Initial import of myriad script from github
downloadMyriad(False)

while(True):

        # run myriad (once)
        myriad = Myriad()
        result = myriad.runOnce()

        # Reload myriad script, in case it changed on the server
        downloadMyriad(True)
        myriad.loadConfig()
        break

