import sys

# This function simply walks a branch of the tree and recursively 
#    adds up all the node sizes found in the branch.
# The computational complexity of the function is O(n + 3).
def calc(base, reps):
	if reps == 1:
                return base
        if base == 1:
                return 1
	total=0
	for i in range(0, base):
		total += calc(base-i, reps-1)
	return total

# While this is the textbook formula for computing the size of
#   particular branch of the tree, the computational complexity
#   of the calculation makes it less desirable than simply 
#   walking the tree (i.e. "calc" function).
# The complexity varies by processor, but is O(2n^2+3) in the 
#   worst case.
def size(base, reps):
	if reps == 1:
		return base
	if base == 1:
		return 1
	return (size(base,reps-1))*((base+(reps-1))/float(reps))

def walk(base, reps, target, accum, stack, basebase, repsreps):
        if reps == 1:
                accum += base
		return accum
        if base == 1:
                accum += 1
		return accum
        for i in range(0, base):
		stack.append(i)
                accum = walk(base-i, reps-1, target, accum, stack, basebase, repsreps)
		if accum > target:
			stack.append(base-i-1)
			#stacklength = len(stack)
			#while len(stack) < repsreps:
			#	stack.append(0)
			offset = repsreps - 1
			index = 0
			for j in stack:
				index += j * (basebase**offset)
				offset -= 1
			print str(index)
			accum = 0
			#while len(stack) > stacklength:
			#	stack.pop()
			stack.pop()
		stack.pop()
        return accum

cores=sys.argv[1]
if len(sys.argv) > 4:
	cores=sys.argv[4]
jobsize=float(calc(int(sys.argv[2]),int(sys.argv[3])))
workunit=jobsize/int(cores)
print "Cores=" + str(cores)
print "Total job size=" + str(jobsize)
print "Target work unit=" + str(workunit)
print "0"
walk(int(sys.argv[2]),int(sys.argv[3]), workunit, 0, [],int(sys.argv[2]),int(sys.argv[3]))



#Slower
#print str(size(int(sys.argv[2]),int(sys.argv[3])))

#Faster
#print str(calc(int(sys.argv[2]),int(sys.argv[3])))
