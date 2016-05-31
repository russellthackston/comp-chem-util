import csv
with open('disp.dat') as f:
	reader = csv.reader(f, delimiter=",")
	disp = list(reader)
for d in disp[0]:
	print d
