import math
import sys
import csv
import itertools

'''
event = {
        'digits' : 5,
        'reps' : 3,
        'start' : 1,
        'end' : 125,
        'modcheck' : [{ 'checkvalue' : 2, 'start' : 3, 'end' : 3 }],
        'equivilence' : [{ 'checkvalue' : 2, 'start' : 3, 'end' : 3 }]
}
'''

modchecks=None
eqchecks=None

# This function derives a single line from the cartesian product with the index 'n'
def entry(n, digits):
	combo = []
        logger.info('# Building entry(' + str(n) + ')')
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
			logger.info(len(tmp)
			logger.info("Error: Parameter not formatted properly: " + rstr)
			logger.info("Are you missing a colon?")
			exit(1)
		num=int(tmp[0])
		ranges=tmp[1]
		if ranges[:1] != "[" or ranges[-1:] != "]":
			logger.info("Error: Parameter not formatted properly: " + rstr)
			logger.info("Is your range properly bracketed (i.e. [])?")
			exit(1)
		if num in results:
			logger.info("Duplicate value '" + str(num) + "' encountered while parsing range '" + str(rangestr) + "'")
			exit(1)
		results[num]=[]
		for range in ranges[1:-1].split(","):
			startend=range.split("-")
			if len(startend) != 2:
				logger.info("Error: Parameter not formatted properly: " + rstr)
				logger.info("Do you have both a start and end value separated with a dash?")
				exit(1)
			start=int(startend[0])
			end=int(startend[1])
			results[num].append([start,end])
	if args.verbose and not args.silent:
		logger.info("# Parsed range " + str(rangestr) + " as " + str(results))
	return results

def eqCheck(e, eqchecks):
	if eqchecks == None or len(eqchecks.keys()) == 0:
		if args.verbose and not args.silent:
			logger.info("# No equivalence checks defined")
		return True
	if args.verbose and not args.silent:
		logger.info("# Equivalence checking is enabled.")
	for k in eqchecks.iterkeys():
		for r in eqchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedEq=sum(e[start-1:end]) != k
			if failedEq:
				if args.verbose and not args.silent:
					logger.info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Failed.")
				return False
			else:
				if args.verbose and not args.silent:
					logger.info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Passed.")
	return True

def modCheck(e, modchecks):
	if modchecks == None or len(modchecks.keys()) == 0:
		if args.verbose and not args.silent:
			logger.info("# No mod checks defined")
		return True
	if args.verbose and not args.silent:
		logger.info("# Mod checking is enabled.")
	for k in modchecks.iterkeys():
		for r in modchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedMod=sum(e[start-1:end])%k != 0
			if failedMod:
				if args.verbose and not args.silent:
					logger.info("# Mod checking %" + str(k) + " for " + str(sub) + ". Failed.")
				return False
			else:
				if args.verbose and not args.silent:
					logger.info("# Mod checking %" + str(k) + " for " + str(sub) + ". Passed.")
	return True

def displacements(e):
	if args.verbose and not args.silent:
		logger.info("# Converting force constants to displacements for " + str(e))
	indexes=[]
	values=[]
	for i, digit in enumerate(e):
		if digit != 0:
			indexes.append(i)
			values.append(digit)
	if len(values) == 0:
		if args.verbose and not args.silent:
			logger.info("# No non-zero values found in list " + str(e))
		return [e]
	if args.verbose and not args.silent:
		logger.info("# Non-zero value(s) " + str(values) + " located in index(es) " + str(indexes))
	prods=[]
	for i, digit in enumerate(values):
		tmp=[]
		for j in range(-1*digit,digit+1,2):
			tmp.append(j)
		prods.append(tmp)
	newrows=map(list, itertools.product(*prods))
	if args.verbose and not args.silent:
		logger.info("# Displacement combinations: " + str(newrows))
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
		logger.info("# Calculated a total of " + str(len(result)) + " displacements")
		logger.info("# Displacement list: " + str(result))
	return result

def main(startIndex,endIndex):
	# Build the array of digits
	digits=[]
	for i in range(0,args.digits):
		digits.append(i)
        logger.info('# Digits array: ' + str(digits))

	rowCount = 0
	i=startIndex
	while i < endIndex:
		e=entry(i, digits)
		if args.verbose and not args.silent:
			logger.info('# Processing index ' + str(i))
		old_i=i
		if args.unfiltered:
			rowCount+=1
			if args.summary:
				rowsIndexes+=1
				rowsForce+=1
				rowsDisp+=len(displacements(e))
			if args.indexes or writeAll:
				fIndexes.write(str(i)+"\n")
			if args.displacements or writeAll:
				lst=displacements(e)
				for l in lst:
					writerDisp.writerow(l)
			if args.forceConstants or writeAll:
				writerForce.writerow(e)
			i+=1
		else:
			# Check if numbers in array total to (args.digits - 1) or greater and skip to next block
			if sum(e) >= (args.digits - 1):
				done = False
				# copy the row
				etemp = e[:]
				# zero the right-most non-zero value
				for idx in range(args.reps-1, -1, -1):
					if etemp[idx] > 0:
						etemp[idx] = 0
						if idx > 0:
							etemp[idx-1] = etemp[idx-1] + 1
						else:
							done = True
						break
				# translate new array into an index
				if done:
					i = endIndex
				else:
					i = 0
					for idx in range(0, args.reps):
						p = args.reps - idx - 1
						i += etemp[idx] * (args.digits**p)
			else:
				i+=1
			if sum(e) <= (args.digits - 1):
				if args.modcheck != None:
					if args.verbose and not args.silent:
						logger.info("# Performing mod check")
					mc = modCheck(e, modchecks)
				else:
					mc = True
				if args.equivalence != None:
					if args.verbose and not args.silent:
						logger.info("# Performing equivalence check")
					ec = eqCheck(e, eqchecks)
				else:
					ec = True
				if (args.modcheck == None and not ec) or (args.equivalence == None and not mc) or (not ec and not mc):
					if args.verbose and not args.silent:
						if not mc:
							logger.info('# Failed mod check')
						if not ec:
							logger.info('# Failed equivalence check')
					rowCount+=1
				else:
					if args.summary:
                                		rowsIndexes+=1
                                		rowsForce+=1
                                		rowsDisp+=len(displacements(e))
					if args.indexes or writeAll:
		                                fIndexes.write(str(i)+"\n")
                		        if args.displacements or writeAll:
						lst=displacements(e)
						for l in lst:
                                			writerDisp.writerow(l)
                		        if args.forceConstants or writeAll:
		                                writerForce.writerow(e)
			else:
				if args.verbose and not args.silent:
					logger.info('# Skipped ' + str(e) + ' due to array total greater than (args.digits - 1)')

	if args.indexes or writeAll:
		fIndexes.close()
        if args.displacements or writeAll:
                fDisp.close()
        if args.forceConstants or writeAll:
                fForce.close()

	if args.summary:
		logger.info("Job Summary")
		logger.info("  Indexes: " + str(rowsIndexes))
		logger.info("  Force Constants: " + str(rowsForce))
		logger.info("  Displacements: " + str(rowsDisp))

	if args.verbose and not args.silent:
		logger.info('# Done creating cartesion product')

def magic(reps, node, nodes):
        return ((2*reps*node)**long((reps**2)/(21*math.sqrt(nodes))))



# ******* Begin main program **********

if args.start:
        sIndex=args.start
else:
        sIndex=0
if args.end:
        eIndex=args.end
else:
        eIndex=args.digits**args.reps

main(sIndex, eIndex)
