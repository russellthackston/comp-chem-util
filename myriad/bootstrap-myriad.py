import requests
import importlib

m_url = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/myriad.py'

def downloadMyriad():
        r = requests.get(m_url)
        f = open('myriad.py', 'w')
        f.write(r.text)
        f.flush()
        f.close()

# Initial import of myriad script from github
downloadMyriad()
import myriad

while(True):

        # run myriad (once)
        myriad.run()

        # Reload myriad script, in case it changed on the server
        downloadMyriad()
        importlib.reload(myriad)
        myriad.loadConfig()
        break

