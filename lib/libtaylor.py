import math
import sys
import argparse
import csv
import itertools

# This function derives a single line from the cartesian product with the index 'n'
def entry(n, digits, reps):
	combo = []
	info('# Building entry(' + str(n) + ')')
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
		info("# No equivalence checks defined")
		return True
	info("# Equivalence checking is enabled.")
	for k in eqchecks.iterkeys():
		for r in eqchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedEq=sum(e[start-1:end]) != k
			if failedEq:
				info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Failed.")
				return False
			else:
				info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Passed.")
	return True

def modCheck(e, modchecks):
	if modchecks == None or len(modchecks.keys()) == 0:
		info("# No mod checks defined")
		return True
	info("# Mod checking is enabled.")
	for k in modchecks.iterkeys():
		for r in modchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedMod=sum(e[start-1:end])%k != 0
			if failedMod:
				info("# Mod checking %" + str(k) + " for " + str(sub) + ". Failed.")
				return False
			else:
				info("# Mod checking %" + str(k) + " for " + str(sub) + ". Passed.")
				pass
	return True

def displacements(e):
	info("# Converting force constants to displacements for " + str(e))
	indexes=[]
	values=[]
	for i, digit in enumerate(e):
		if digit != 0:
			indexes.append(i)
			values.append(digit)
	if len(values) == 0:
		info("# No non-zero values found in list " + str(e))
		return [e]
	info("# Non-zero value(s) " + str(values) + " located in index(es) " + str(indexes))
	prods=[]
	for i, digit in enumerate(values):
		tmp=[]
		for j in range(-1*digit,digit+1,2):
			tmp.append(j)
		prods.append(tmp)
	newrows=map(list, itertools.product(*prods))
	info("# Displacement combinations: " + str(newrows))
	# Build each new displacement row by copying the force constant row then overwriting
	#   the non-zero values with the calculated values
	result=[]
	for row in newrows:
		# make a copy of 'e'
		r=list(e)
		for i, index in enumerate(indexes):
			r[index]=row[i]
		result.append(r)
	info("# Calculated a total of " + str(len(result)) + " displacements")
	info("# Displacement list: " + str(result))
	return result

