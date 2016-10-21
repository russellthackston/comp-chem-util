import math
import sys
import argparse
import csv
import itertools

logfunction = None
parseRanges = None

def setLogFunction(fx):
	global logfunction
	logfunction = fx

def log(msg):
	global logfunction
	if logfunction != None:
		logfunction(msg)

def setParseRanges(fx):
	global parseRanges
	parseRanges = fx

# This function derives a single line from the cartesian product with the index 'n'
def entry(n, digits, reps):
	combo = []
	log('# Building entry(' + str(n) + ')')
	exp=1
	while n > 0:
		div=len(digits)**exp
		digit=(n%div)
		n-=digit
		digit=digit/len(digits)**(exp-1)
		combo.insert(0,int(digit))
		exp+=1
	for i in range(0,reps-len(combo)):
		combo.insert(0,0)
	return combo

def eqCheck(e, eqchecks):
	if eqchecks == None or len(eqchecks.keys()) == 0:
		log("# No equivalence checks defined")
		return True
	log("# Equivalence checking is enabled.")
	for k in eqchecks.iterkeys():
		for r in eqchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedEq=sum(e[start-1:end]) != k
			if failedEq:
				log("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Failed.")
				return False
			else:
				log("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Passed.")
	return True

def modCheck(e, modchecks):
	if modchecks == None or len(modchecks.keys()) == 0:
		log("# No mod checks defined")
		return True
	log("# Mod checking is enabled.")
	for k in modchecks.iterkeys():
		for r in modchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedMod=sum(e[start-1:end])%k != 0
			if failedMod:
				log("# Mod checking %" + str(k) + " for " + str(sub) + ". Failed.")
				return False
			else:
				log("# Mod checking %" + str(k) + " for " + str(sub) + ". Passed.")
				pass
	return True

def displacements(e):
	log("# Converting force constants to displacements for " + str(e))
	indexes=[]
	values=[]
	for i, digit in enumerate(e):
		if digit != 0:
			indexes.append(i)
			values.append(digit)
	if len(values) == 0:
		log("# No non-zero values found in list " + str(e))
		return [e]
	log("# Non-zero value(s) " + str(values) + " located in index(es) " + str(indexes))
	prods=[]
	for i, digit in enumerate(values):
		tmp=[]
		for j in range(-1*digit,digit+1,2):
			tmp.append(j)
		prods.append(tmp)
	newrows=map(list, itertools.product(*prods))
	log("# Displacement combinations: " + str(newrows))
	# Build each new displacement row by copying the force constant row then overwriting
	#   the non-zero values with the calculated values
	result=[]
	for row in newrows:
		# make a copy of 'e'
		r=list(e)
		for i, index in enumerate(indexes):
			r[index]=row[i]
		result.append(r)
	log("# Calculated a total of " + str(len(result)) + " displacements")
	log("# Displacement list: " + str(result))
	return result

def main(event, startIndex, endIndex, indexes, force, disp):
	global parseRanges

	modchecks=None
	eqchecks=None

	# Set up summary variables
	rowsIndexes = 0
	rowsForce = 0
	rowsDisp = 0

	# Logical error checking with config
	if 'equivalence' in event and not 'modcheck' in event:
		log("# Error: equivalence check defined without mod check")
		exit(1)

	# Build the array of digits
	digits=[]
	for i in range(0, event['digits']):
		digits.append(i)
	log('# Digits array: ' + str(digits))

	# If mod checks are enabled, build a list of checks to be performed
	if 'modcheck' in event:
		modchecks=parseRanges(event['modcheck'])
		log("# Parsed mod check " + str(event['modcheck']) + " into " + str(modchecks))

	# If equivalence checks are enabled, build a list of checks to be performed
	if 'equivalence' in event:
		eqchecks=parseRanges(event['equivalence'])
		log("# Parsed mod check " + str(event['equivalence']) + " into " + str(eqchecks))

	# Open the output streams
	fIndexes = open(indexes, 'w')
	fForce = open(force, 'w')
	writerForce = csv.writer(fForce)
	fDisp = open(disp, 'w')
	writerDisp = csv.writer(fDisp)

	rowCount = 0
	i=startIndex
	while i < endIndex:
		e=entry(i, digits, event['reps'])
		log('# Processing index ' + str(i))
		old_i=i

		# Check if numbers in array total to (e['digits'] - 1) or greater and skip to next block
		if sum(e) >= (event['digits'] - 1):
			done = False
			# copy the row
			etemp = e[:]
			# zero the right-most non-zero value
			for idx in range(event['reps']-1, -1, -1):
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
				for idx in range(0, event['reps']):
					p = event['reps'] - idx - 1
					i += etemp[idx] * (event['digits']**p)
		else:
			i+=1
		if sum(e) <= (event['digits'] - 1):
			keeper = True

			# if a mod check is defined, run it
			if 'modcheck' in event:
				log("# Performing mod check")
				passedModCheck = modCheck(e, modchecks)
			else:
				passedModCheck = True

			# if the mod check fails, you may need to check for an Eq check
			# Failing the mod check but passing the Eq check will get the record included
			if not passedModCheck:
				log('# Failed mod check')
				if 'equivalence' in event:
					log("# Performing equivalence check")
					passedEqCheck = eqCheck(e, eqchecks)
					if not passedEqCheck:
						log('# Failed equivalence check')
						keeper = False
				else:
					keeper = False
			if not keeper:
				log('# Bad record: ' + str(e))
				rowCount+=1
			else:
				log('# Good record: ' + str(e))
				fIndexes.write(str(i)+"\n")
				lst=displacements(e)
				for l in lst:
					writerDisp.writerow(l)
				writerForce.writerow(e)
		else:
			log('# Skipped ' + str(e) + ' due to array total greater than (e["digits"] - 1)')
			pass

	fIndexes.close()
	fDisp.close()
	fForce.close()

	log('# Done creating cartesion product')

def magic(reps, node, nodes):
	return ((2*reps*node)**long((reps**2)/(21*math.sqrt(nodes))))
