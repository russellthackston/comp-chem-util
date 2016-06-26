import sys
import math
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
def partition(base, reps, target, accum, stack, basebase, repsreps, result):
        if reps == 1:
                accum += base
		return accum
        if base == 1:
                accum += 1
		return accum
        for i in range(0, base):
		stack.append(i)
                accum = partition(base-i, reps-1, target, accum, stack, basebase, repsreps, result)
		if accum >= target:
			stack.append(base-i-1)
			offset = repsreps - 1
			index = 0
			for j in stack:
				index += j * (basebase**offset)
				offset -= 1
			result.append(index)
			accum = 0
			stack.pop()
		stack.pop()
        return accum

def get(event, context):
        # Get the command line parameters
        cores=str(event['cores'])
        # Calculate the total job size
        base=str(event['base'])
        reps=str(event['reps'])
        jobsize=float(size(int(base),int(reps)))
        # Calculate the size of each work unit
        workunit=int(math.ceil(jobsize/int(cores)))
        logger.info("Cores=" + str(cores))
        logger.info("Total job size=" + str(jobsize))
        logger.info("Target work unit=" + str(workunit))
        logger.info("Starting indexes:")
        result = ["0"]
        partition(int(base),int(reps), workunit, 0, [],int(base),int(reps), result)
        result.append(str(int(math.pow(int(base),int(reps)))))
        logger.info(str(result))
        return str(result)
