import requests

r = requests.get('https://s3.amazonaws.com/psi4share/SNS/mk_input_dat.py')
print r.text
