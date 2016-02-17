import math
import sys
import argparse
import os.path

parser = argparse.ArgumentParser(description='Generate output row(s) of a cartesian product by index.')
parser.add_argument("-s", "--sets", dest="sets", help="File containing sets for cartesian product. One line per set with each set a comma-delimited list of values.", type=str)
parser.add_argument("-f", "--first", dest="first", help="The first index to generate (zero-based). If both --first and --last are omitted, all rows will be generated.", type=int)
parser.add_argument("-l", "--last", dest="last", help="The last index to generate. If both --first and --last are omitted, all rows will be generated.", type=int)
parser.add_argument("-n", "--numeric", dest="numeric", help="Treat list values as numeric (integers).", action='store_true')
parser.add_argument("-b", "--bare", dest="bare", help="Print using bare format (no square brackets or spaces).", action='store_true')
args=parser.parse_args()

# Build variables
firstIndex=0
lastIndex=1
if args.first:
	firstIndex=int(args.first)
if not args.sets:
	args.sets="sets.csv"

# Build the array of sets (array of arrays) from the file
sets=[]
if not os.path.isfile(args.sets):
	print "Error: " + args.sets + " not found."
	exit(1)
with open(args.sets) as f:
	for line in f:
		values=line.strip().split(",")
		if args.numeric:
			sets.append(map(int,values))
		else:
			sets.append(values)
		lastIndex *= len(values)

# Error checking on sets file
if len(sets) == 0:
	print "Error: No sets found in " + args.sets
	exit(1)

sets=list(reversed(sets))

# Build list of mod values
m=[1]
for idx, set in enumerate(sets):
	l=len(set)
	accum=l*m[idx]
	m.append(accum)
listCount=len(sets)

# Clean up the lengths list
if args.last:
        lastIndex=int(args.last)

for index in range(firstIndex, lastIndex):
	line=[]
	for i, set in reversed(list(enumerate(sets))):
		x=int(math.floor((index%m[i+1])/m[i]))
		line.append(set[x])
	if args.bare:
		print str(line)[1:-1].replace(' ', '').replace("'","")
	else:
		print line
