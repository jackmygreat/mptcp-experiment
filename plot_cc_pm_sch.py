#!/usr/bin/python3.7

import os
import re
import numpy as np
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
from matplotlib import cm

fig = plt.figure(figsize=(32,30))
ax = fig.gca(projection='3d')

directory = '.'
index = 0
folders = []

for file in os.listdir(directory):
     filename = os.fsdecode(file)
     if os.path.isfile(filename):
        continue
     if '_' not in filename:
        continue
     groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)', filename)
     print(f"{groups.group(1)} {groups.group(2)} {groups.group(3)}")
     index += 1
     folders.append(filename)
     with open(f"{filename}/results/iperf.data", "r") as f:
        lines = f.readlines()
        time = []
        thr = []
        for line in lines:
                sp = line.split()
                time.append(float(sp[0]))
                thr.append(float(sp[1]))
        ax.plot(time, thr, zs = index, zdir='x')

ax.set_xticks(range(len(folders)), folders)
ax.legend()
ax.azim = -10
ax.dist = 8
ax.elev = 20
fig.savefig(f'3d.png')
#plt.show()
