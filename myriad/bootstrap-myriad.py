import requests
import importlib

def downloadMyriad():
        r = requests.get('https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/myriad.py')
        f = open('myriad.py', 'w')
        f.write(r.text)
        f.flush()
        f.close()

while(True):
        downloadMyriad()
        import myriad
        myriad.loadConfig()
        importlib.reload(module)
        break
