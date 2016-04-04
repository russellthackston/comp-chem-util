import sys

def calc(base, reps):
	if reps == 1 or base == 1:
		s = size(base, reps)
		#print str(base) + "," + str(reps) + "=" + str(s)
		return s
	total=0
	for i in range(0, base):
		total += calc(base-i, reps-1)
	return total

def size(base, reps):
	if reps == 1:
		return base
	if base == 1:
		return 1
	y = (base+(reps-1))/float(reps)
	x = size(base,reps-1)
	return (size(base,reps-1))*((base+(reps-1))/float(reps))

#print str(size(int(sys.argv[1]),int(sys.argv[2])))
print str(calc(int(sys.argv[1]),int(sys.argv[2])))
