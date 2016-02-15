import math
import sys
import argparse
import csv
import itertools

parser = argparse.ArgumentParser(description='Generate a Taylor series.', epilog='Example #1: "python taylor.py 5 24" will print the product of 24 repetitions of [0,1,2,3,4]. Example #2: "python taylor.py 5 24 -m 2:[17-23] -o 5x24.txt" will write the product of 24 repetitions of [0,1,2,3,4] to a file named 5x24.txt, skipping rows that fail a mod 2 check of the sum of digits 17-23.')
parser.add_argument("digits", help="The number of digits in the array [0..digits]", type=int)
parser.add_argument("reps", help="The number of repetitions of the set", type=int)
parser.add_argument("-s", "--start", help="Only print lines with indexes greater than or equal to (digits^start)", type=int)
parser.add_argument("-e", "--end", help="Only print lines with indexes less than or equal to (digits^end)", type=int)
parser.add_argument("-m", "--modcheck", help="Enables a mod check of one of more subsets of digits", type=str)
parser.add_argument("-q", "--equivalence", help="Enables an equivalence check of one or more subsets of digits", type=str)
parser.add_argument("-o", "--outputFile", help="Write output to file", type=str)
parser.add_argument("-d", "--displacements", help="Generate displacements (instead of force constants)", action="store_true")
parser.add_argument("-i", "--indexesOnly", help="Only write row indexes to output", action="store_true")
parser.add_argument("-l", "--silent", help="Suppress all output to stdout", action="store_true")
parser.add_argument("-u", "--unfiltered", help="Skip the filtering step and produce a complete cartesian product", action="store_true")
parser.add_argument("-v", "--verbose", help="Produce verbose output", action="store_true")
parser.add_argument('--version', action='version', version='Taylor Series generation script v1.0. Latest version and full documentation available at https://github.com/russellthackston/comp-chem-util in the 'misc' folder. Report any bugs or issues at the above web address.')
args=parser.parse_args()

modchecks=None
eqchecks=None

# This function derives a single line from the cartesian product with the index 'n'
def entry(n, digits):
	combo = []
	if args.verbose and not args.silent:
		print '# Building entry(' + str(n) + ')'
	exp=1
	while n > 0:
		div=len(digits)**exp
		digit=(n%div)
		n-=digit
		digit=digit/len(digits)**(exp-1)
		combo.insert(0,int(digit))
		exp+=1
	for i in range(0,args.reps-len(combo)):
		combo.insert(0,0)
	return combo

def parseRanges(rangestr):
	# n:[start-end,start-end]?n:[start-end]?n:[start-end]
	# Ex.- 4:[1-2,3-4]?3:[5-6]

	results=dict()
	# Split parameter on the question mark symbol (?)
	for rstr in rangestr.split("?"):
		tmp=rstr.split(":")
		if len(tmp) != 2:
			print len(tmp)
			print "Error: Parameter not formatted properly: " + rstr
			print "Are you missing a colon?"
			exit(1)
		num=int(tmp[0])
		ranges=tmp[1]
		if ranges[:1] != "[" or ranges[-1:] != "]":
			print "Error: Parameter not formatted properly: " + rstr
			print "Is your range properly bracketed (i.e. [])?"
			exit(1)
		if num in results:
			print "Duplicate value '" + str(num) + "' encountered while parsing range '" + str(rangestr) + "'"
			exit(1)
		results[num]=[]
		for range in ranges[1:-1].split(","):
			startend=range.split("-")
			if len(startend) != 2:
				print "Error: Parameter not formatted properly: " + rstr
				print "Do you have both a start and end value separated with a dash?"
				exit(1)
			start=int(startend[0])
			end=int(startend[1])
			results[num].append([start,end])
	if args.verbose and not args.silent:
		print "# Parsed range " + str(rangestr) + " as " + str(results)
	return results

def eqCheck(e, eqchecks):
	if eqchecks == None or len(eqchecks.keys()) == 0:
		if args.verbose and not args.silent:
			print "# No equivalence checks defined"
		return True
	if args.verbose and not args.silent:
		print "# Equivalence checking is enabled."
	for k in eqchecks.iterkeys():
		for r in eqchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedEq=sum(e[start-1:end]) != k
			if failedEq:
				if args.verbose and not args.silent:
					print "# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Failed."
				return False
			else:
				if args.verbose and not args.silent:
					print "# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Passed."
	return True

def modCheck(e, modchecks):
	if modchecks == None or len(modchecks.keys()) == 0:
		if args.verbose and not args.silent:
			print "# No mod checks defined"
		return True
	if args.verbose and not args.silent:
		print "# Mod checking is enabled."
	for k in modchecks.iterkeys():
		for r in modchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedMod=sum(e[start-1:end])%k != 0
			if failedMod:
				if args.verbose and not args.silent:
					print "# Mod checking %" + str(k) + " for " + str(sub) + ". Failed."
				return False
			else:
				if args.verbose and not args.silent:
					print "# Mod checking %" + str(k) + " for " + str(sub) + ". Passed."
	return True

def displacements(e):
	if args.verbose and not args.silent:
		print "# Converting force constants to displacements for " + str(e)
	indexes=[]
	values=[]
	for i, digit in enumerate(e):
		if digit != 0:
			indexes.append(i)
			values.append(digit)
	if len(values) == 0:
		if args.verbose and not args.silent:
			print "# No non-zero values found in list " + str(e)
		return [e]
	if args.verbose and not args.silent:
		print "# Non-zero value(s) " + str(values) + " located in index(es) " + str(indexes)
	prods=[]
	for i, digit in enumerate(values):
		tmp=[]
		for j in range(-1*digit,digit+1,2):
			tmp.append(j)
		prods.append(tmp)
	newrows=map(list, itertools.product(*prods))
	if args.verbose and not args.silent:
		print "# Displacement combinations: " + str(newrows)
	# Build each new displacement row by copying the force constant row then overwriting
	#   the non-zero values with the calculated values
	result=[]
	for row in newrows:
		# make a copy of 'e'
		r=list(e)
		for i, index in enumerate(indexes):
			r[index]=row[i]
		result.append(r)
	if args.verbose and not args.silent:
		print "# Calculated a total of " + str(len(result)) + " displacements"
		print "# Displacement list: " + str(result)
	return result

def main(startIndex,endIndex):
	# Build the array of digits
	digits=[]
	for i in range(0,args.digits):
		digits.append(i)
	if args.verbose and not args.silent:
		print '# Digits array: ' + str(digits)

	# If mod checks are enabled, build a list of checks to be performed
	if args.modcheck:
		modchecks=parseRanges(args.modcheck)
		if args.verbose and not args.silent:
			print "# Parsed mod check " + str(args.modcheck) + " into " + str(modchecks)

	# If equivalence checks are enabled, build a list of checks to be performed
	if args.equivalence:
		eqchecks=parseRanges(args.equivalence)
		if args.verbose and not args.silent:
			print "# Parsed mod check " + str(args.equivalence) + " into " + str(eqchecks)

	# Open the output file, if requested
	if args.outputFile:
		f = open(args.outputFile, 'w')
		writer = csv.writer(f)

	rowCount = 0
	i=(len(digits)**startIndex)-1
	while i < len(digits)**endIndex:
		e=entry(i, digits)
		if args.verbose and not args.silent:
			print '# Processing index ' + str(i)
		old_i=i
		if args.unfiltered:
			rowCount+=1
			if args.outputFile:
				if args.indexesOnly:
					writer.writerow([i])
				else:
					if args.displacements:
						lst=displacements(e)
						for l in lst:
							writer.writerow(l)
					else:
						writer.writerow(e)
				if rowCount % args.reps == 0 and not args.silent:
					sys.stdout.write('.')
					sys.stdout.flush()
			else:
				if args.indexesOnly:
					print(i)
				else:
					if args.displacements:
						lst=displacements(e)
						for l in lst:
							print str(l)[1:-1].replace(' ','')
					else:
						print str(e)[1:-1].replace(' ','')
			i+=1
		else:
			# Check if numbers in array total to 4 or greater and skip to next block
			if sum(e) >= 4:
				tmp=0
				left=args.reps-1
				for j in range(0, len(e)-1):
					tmp+=e[j]
					if tmp >= 4:
						left=j
						break
				right=0
				for j in range(len(e)-1, -1, -1):
					if e[j] != 0:
						right=j
						break
				j=max(min(left,right),0)
				index=(len(e)-j)
				k=len(digits)**index
				l=(i+k)%(len(digits)**index)
				i+=(k-l)
			else:
				i+=1
			if sum(e) <= 4:
				if args.modcheck != None:
					if args.verbose and not args.silent:
						print "# Performing mod check"
					mc = modCheck(e, modchecks)
				else:
					mc = True
				if args.equivalence != None:
					if args.verbose and not args.silent:
						print "# Performing equivalence check"
					ec = eqCheck(e, eqchecks)
				else:
					ec = True
				if (args.modcheck == None and not ec) or (args.equivalence == None and not mc) or (not ec and not mc):
					if args.verbose and not args.silent:
						if not mc:
							print '# Failed mod check'
						if not ec:
							print '# Failed equivalence check'
					rowCount+=1
				else:
					if args.outputFile:
						if args.indexesOnly:
							writer.writerow([i])
						else:
							if args.displacements:
								lst=displacements(e)
								for l in lst:
									writer.writerow(l)
							else:
								writer.writerow(e)
						if rowCount % args.reps == 0 and not args.silent:
							sys.stdout.write('.')
							sys.stdout.flush()
					else:
						if args.indexesOnly:
							print(i)
						else:
							if args.displacements:
								lst=displacements(e)
								for l in lst:
									print str(l)[1:-1].replace(' ','')
							else:
								print str(e)[1:-1].replace(' ','')
			else:
				if args.verbose and not args.silent:
					print '# Skipped ' + str(e) + ' due to array total greater than 4'

	if args.outputFile:
		f.close()
		if not args.silent:
			print ''
	if args.verbose and not args.silent:
		print '# Done creating cartesion product'

# Set up indexes
if args.start:
	sIndex=args.start
else:
	sIndex=0
if args.end:
	eIndex=args.end
else:
	eIndex=args.reps

main(sIndex, eIndex)
