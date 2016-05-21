import sys,math

# This is the textbook formula for computing the size of
#   particular branch of the tree, based on the formula for
#   a figurate number (specifically r-topic numbers).
def size(base, reps):
	if reps == 1:
		return base
	if base == 1:
		return 1
	return (size(base,reps-1))*((base+(reps-1))/float(reps))

# Walks the entire tree and partitions the tree's nodes into
#   similarly sized chunks based on the the desired number of nodes.
def partition(base, reps, target, accum, stack, basebase, repsreps):
        if reps == 1:
                accum += base
		return accum
        if base == 1:
                accum += 1
		return accum
        for i in range(0, base):
		stack.append(i)
                accum = partition(base-i, reps-1, target, accum, stack, basebase, repsreps)
		if accum >= target:
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

# Get the command line parameters
cores=sys.argv[1]
if len(sys.argv) > 4:
	cores=sys.argv[4]
# Calculate the total job size
jobsize=float(size(int(sys.argv[2]),int(sys.argv[3])))
# Calculate the size of each work unit
workunit=int(math.ceil(jobsize/int(cores)))
print "Cores=" + str(cores)
print "Total job size=" + str(jobsize)
print "Target work unit=" + str(workunit)
print "Starting indexes:"
print "0"
partition(int(sys.argv[2]),int(sys.argv[3]), workunit, 0, [],int(sys.argv[2]),int(sys.argv[3]))

