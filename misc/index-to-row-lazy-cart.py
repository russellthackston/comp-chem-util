import sys

e = sys.argv[1].split(",")
i = 0
for idx in range(0, len(e)):
	p = len(e) - idx - 1
	i += int(e[idx]) * (int(sys.argv[2])**p)
print i
