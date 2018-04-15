import math
import sys
import argparse
import csv
import itertools

sys.path.insert(0, '../lib')
import libtaylor

parser = argparse.ArgumentParser(description='Generate a Taylor series.', epilog='Example: "python taylor.py 5 24" will print the product of 24 repetitions of [0,1,2,3,4].')
parser.add_argument("digits", help="The number of digits in the array [0..digits]", type=int)
parser.add_argument("reps", help="The number of repetitions of the set", type=int)
parser.add_argument("-s", "--start", help="Only print lines with indexes greater than or equal to 'start'", type=int)
parser.add_argument("-e", "--end", help="Only print lines with indexes less than or equal to 'end'", type=int)
parser.add_argument("-m", "--modcheck", help="Enables a mod check of one of more subsets of digits (first digit is index 1). Not passing the mod check excludes the row. Expects this value to be in the format '-m d:[s-e]' where 'd' is the mod check value, 's' is the start index, and 'e' is the end index.", type=str)
parser.add_argument("-q", "--equivalence", help="Enables an equivalence check of one or more subsets of digits (first digit is index 1). Passing the equivilence check, after failing a mod check, includes the row. Expects this value to be in the format '-m q:[s-e]' where 'q' is the equivilence check value, 's' is the start index, and 'e' is the end index.", type=str)
parser.add_argument("-p", "--parallel", help="Calculates the --start and --end values based on the provided node number and number of nodes. Expected format is '--p (node number):(number of nodes)'", type=str)
parser.add_argument("-f", "--forceConstants", help="Write force constant values to force.txt", action="store_true")
parser.add_argument("-d", "--displacements", help="Write displacement values to disp.txt", action="store_true")
parser.add_argument("-i", "--indexes", help="Write row indexes to indexes.txt", action="store_true")
parser.add_argument("-l", "--silent", help="Suppress all output to stdout", action="store_true")
parser.add_argument("-u", "--unfiltered", help="Skip the filtering step and produce a complete cartesian product", action="store_true")
parser.add_argument("-v", "--verbose", help="Produce verbose output", action="store_true")
parser.add_argument("--debug", help="Sets up the job but does not run it. Prints debug info instead", action="store_true")
parser.add_argument("--summary", help="Only print summary information (i.e. number of rows in output files)", action="store_true")
parser.add_argument('--version', action='version', version='Taylor Series generation script v1.0. Latest version and full documentation available at https://github.com/russellthackston/comp-chem-util in the "misc" folder. Report any bugs or issues at the above web address.')
args=parser.parse_args()


def info(msg):
	if args.verbose and not args.silent:
		print(msg)

def parseRanges(rangestr):
	# n:[start-end,start-end]?n:[start-end]?n:[start-end]
	# Ex.- 4:[1-2,3-4]?3:[5-6]

	results=dict()
	# Split parameter on the question mark symbol (?)
	for rstr in rangestr.split("?"):
		tmp=rstr.split(":")
		if len(tmp) != 2:
			info(len(tmp))
			info("Error: Parameter not formatted properly: " + rstr)
			info("Are you missing a colon?")
			exit(1)
		num=int(tmp[0])
		ranges=tmp[1]
		if ranges[:1] != "[" or ranges[-1:] != "]":
			info("Error: Parameter not formatted properly: " + rstr)
			info("Is your range properly bracketed (i.e. [])?")
			exit(1)
		if num in results:
			info("Duplicate value '" + str(num) + "' encountered while parsing range '" + str(rangestr) + "'")
			exit(1)
		results[num]=[]
		for range in ranges[1:-1].split(","):
			startend=range.split("-")
			if len(startend) != 2:
				info("Error: Parameter not formatted properly: " + rstr)
				info("Do you have both a start and end value separated with a dash?")
				exit(1)
			start=int(startend[0])
			end=int(startend[1])
			results[num].append([start,end])
	info("# Parsed range " + str(rangestr) + " as " + str(results))
	return results

# ******* Begin main program **********

# set the log function
libtaylor.setLogFunction(info)
libtaylor.setParseRanges(parseRanges)

# digits are zero based so add 1 to user input
args.digits += 1

# Set up indexes
# If parallelization is enabled, calculate the start and end based on the node number
#   and number of nodes
if args.parallel:
	if args.verbose and not args.silent:
		print 'Calculating parallelization values'
	p = args.parallel.split(":");
	if len(p) != 2:
		print "Error: Parameter not formatted properly: " + args.parallel
		print "Is your start/end node list properly formatted as '(start):(end)'?"
		exit(1)
	if int(p[0]) == 1:
		# If it's the first node in the node set, then the start index is 0
		sIndex = 0
		if args.verbose and not args.silent:
			print 'First node. Setting sIndex to 0'
	else:
		sIndex = libtaylor.magic(args.reps, int(p[0]), int(p[1]))
		if args.verbose and not args.silent:
			print 'sIndex set to ' + str(sIndex)
	if int(p[0]) == int(p[1]):
		# if it's the last node in the node set, then the end is the last index
		eIndex = args.digits**args.reps
		if args.verbose and not args.silent:
			print 'Last node. eIndex set to ' + str(eIndex)
	else:
		eIndex = libtaylor.magic(args.reps, int(p[0])+1, int(p[1]))
		if args.verbose and not args.silent:
			print 'eIndex set to ' + str(eIndex)

	if sIndex == eIndex:
		eIndex = eIndex + 1
else:
	if args.start:
		sIndex=args.start
	else:
		sIndex=0
	if args.end:
		eIndex=args.end
	else:
		eIndex=args.digits**args.reps

if args.debug:
	print str(args)
	print "sIndex="+str(sIndex)
	print "eIndex="+str(eIndex)
	exit(0)

event = dict()
if args.equivalence:
	event['equivalence'] = args.equivalence
if args.modcheck:
	event['modcheck'] = args.modcheck
event['digits'] = args.digits
event['reps'] = args.reps

libtaylor.main(event, sIndex, eIndex, 'indexes.txt', 'force.txt', 'disp.txt')
