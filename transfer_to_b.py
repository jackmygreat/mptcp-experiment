import os


f = open("iperf.data", "w+")

with open("d", "r+") as ff:
	lines = ff.readlines()
	for line in lines:
		words = line.split("\t")
		f.write(words[0].strip())
		f.write("\t")
		f.write(str( float(words[1].strip().rstrip("\n")) * 8))
		f.write("\n")

f.close()

