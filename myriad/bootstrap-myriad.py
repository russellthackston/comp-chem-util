import requests
import importlib
from enum import Enum

m_server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'

def downloadMyriad():
        downloadMyriadFile('libmyriad.py')
        downloadMyriadFile('myriad.py')
        import libmyriad
        import myriad
        importlib.reload(libmyriad)
        importlib.reload(myriad)

def downloadMyriadFile(filename):
        r = requests.get(m_server + filename)
        f = open(filename, 'w')
        f.write(r.text)
        f.flush()
        f.close()

# Initial import of myriad script from github
downloadMyriad()

while(True):

        # run myriad (once)
        result = myriad.runOnce()

        # Reload myriad script, in case it changed on the server
        downloadMyriad()
        myriad.loadConfig()
        break

