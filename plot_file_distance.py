#!/usr/bin/python3.7

import os
import re
import numpy as np
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
from matplotlib import cm

def plot(fig, ax, figure_name, x, y, z, xlabel, ylabel, zlabel):
        y = np.array(y)
        x = np.array(x)
        z = np.array(z)
    
        ax.plot_trisurf(x, y, z, color='yellow', antialiased=False, alpha=0.5, linewidth = 0.25)
        ax.set(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
                title=figure_name)
        fig.tight_layout()

        fig.savefig(f'{figure_name}.png')

def plot_dtime(algo, distances, files_size, downloads_time):
        fig = plt.figure(num=1, clear=True)
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.invert_xaxis()
        ax.azim = -40
        ax.dist = 10
        ax.elev = 20

        distances = [float(x) for x in distances]
        files_size = [float(x) for x in files_size]
        downloads_time = [float(x) for x in downloads_time]
        
        plot(fig, ax, f"{algo}_dtime", files_size, distances, downloads_time, "File Size[MB]", "Distance [m]", "Download time [s]")

def plot_throughput(algo, distances, files_size, throughputs):
        fig = plt.figure(num=1, clear=True)
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.azim = -40
        ax.dist = 10
        ax.elev = 20

        distances = [float(x) for x in distances]
        files_size = [float(x) for x in files_size]
        throughputs = [float(x) for x in throughputs]

        ax.set_ylim(max(distances), min(distances))
        plot(fig, ax, f"{algo}_throughput", files_size, distances, throughputs, "File Size[MB]", "Distance [m]", "Throughput [Mb/s]")

def plot_algo(algo, results):
        thr_fig, thr_ax = plt.subplots(2, 2, figsize=(10,10), subplot_kw=dict(projection='3d'))
        
        for i in range(4):
                thr_ax[i // 2, i % 2].azim = -40
                thr_ax[i // 2, i % 2].dist = 10
                thr_ax[i // 2, i % 2].elev = 20
                thr_ax[i // 2, i % 2].set(xlabel="File Size[MB]", ylabel="Distance [m]", zlabel="Throughput [Mb/s]",
                           title=f"{algo} Throughput")

        dt_fig = plt.figure(clear=True)
        dt_ax = dt_fig.add_subplot(2, 2, 1, projection='3d')
        dt_ax.azim = -40
        dt_ax.dist = 10
        dt_ax.elev = 20
        dt_ax.invert_xaxis()
        dt_ax.set(xlabel="File Size[MB]", ylabel="Distance [m]", zlabel="Download time [s]",
                      title=f"{algo} Download Time")

        colors = ["yellow", "red", "blue", "black"]
        cmap = ['spring', 'summer', 'autumn', 'winter']
        index = -1
        for specific_algo, folders in results.items():
                index += 1
                distances = []
                download_time = []
                throughput = []
                file_size = []
                for folder in folders:
                    iperf_data = extract_iperf_data(folder)
                    download_time.append(iperf_data["time"])
                    throughput.append(iperf_data["throughput"])
                    file_size.append(iperf_data["file_size"])          
                    groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', folder)
                    distances.append(groups.group(5).split('m')[0])
                distances = [float(x) for x in distances]
                files_size = [float(x) for x in file_size]
                throughputs = [float(x) for x in throughput]
                downloads_time = [float(x) for x in download_time]

                thr_ax.set_ylim(max(distances), min(distances))

                distances = np.array(distances)
                files_size = np.array(files_size)
                throughputs = np.array(throughputs)
                downloads_time = np.array(downloads_time)
   
                if False: 
                        thr_ax.plot_trisurf(files_size, distances, throughputs, cmap=cmap[index], antialiased=False, alpha=0.5, linewidth = 0.25, vmin = throughputs.min() * 0.5, vmax = throughputs.max() * 2.5)
                        dt_ax.plot_trisurf(files_size, distances, downloads_time, cmap=cmap[index], antialiased=False, alpha=0.5, linewidth = 0.25, vmin = downloads_time.min() * 0.5, vmax = downloads_time.max() * 2.5)
                else:
                        thr_ax[0, index].plot_trisurf(files_size, distances, throughputs, color=colors[index], antialiased=False, alpha=0.5, linewidth = 0.25)
                        dt_ax[0, index].plot_trisurf(files_size, distances, downloads_time, color=colors[index], antialiased=False, alpha=0.5, linewidth = 0.25)
        thr_fig.tight_layout()
        thr_fig.savefig(f'{algo}_throughputs.png')
        
        dt_fig.tight_layout()
        dt_fig.savefig(f'{algo}_dtime.png')

               

def extract_iperf_data(folder):
        with open(f"{folder}/results/iperf.txt", "r") as f:
                lines = f.readlines()
                splitted_data = lines[-1].split(" ")
                valid_data = []
                for data in splitted_data:
                        if data == "" or len(data) == 0:
                                continue
                        valid_data.append(data)
                splitted_data = valid_data
                time = splitted_data[2].split('-')[1]
                print(f"{time} {splitted_data[4]} {splitted_data[6]}")
                return {
                   "time": time,
                   "file_size": splitted_data[4],
                   "throughput": splitted_data[6]
                } 

directory = os.fsencode(".")

folders = {}

algo = {}

for file in os.listdir(directory):
     filename = os.fsdecode(file)
     if os.path.isfile(filename):
        continue
     groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', filename)
     print(f"{groups.group(1)} {groups.group(2)} {groups.group(3)} {groups.group(4)} {groups.group(5)}")
     
     old_folders = folders.get(f"{groups.group(1)}_{groups.group(2)}_{groups.group(3)}", None)
     if old_folders == None:
        folders[f"{groups.group(1)}_{groups.group(2)}_{groups.group(3)}"] = [filename]
     else: 
        fold = folders[f"{groups.group(1)}_{groups.group(2)}_{groups.group(3)}"]
        fold.append(filename)
        folders[f"{groups.group(1)}_{groups.group(2)}_{groups.group(3)}"] = fold

     algo_dict = algo.get(f"{groups.group(1)}", None)
     if algo_dict == None:
         dict_v = {}
         dict_v[f"{groups.group(2)}_{groups.group(3)}"] = [filename]
         algo[f"{groups.group(1)}"] = dict_v
     else:
         specific_algo = algo_dict.get(f"{groups.group(2)}_{groups.group(3)}", None)
         if specific_algo == None:
             algo[f"{groups.group(1)}"][f"{groups.group(2)}_{groups.group(3)}"] = [filename]
         else:
             tmp = algo[f"{groups.group(1)}"][f"{groups.group(2)}_{groups.group(3)}"]
             tmp.append(filename)
             algo[f"{groups.group(1)}"][f"{groups.group(2)}_{groups.group(3)}"] = tmp


for key, value in folders.items():
        distances = []
        download_time = []
        throughput = []
        file_size = []
        for folder in value:
                iperf_data = extract_iperf_data(folder)
                download_time.append(iperf_data["time"])
                throughput.append(iperf_data["throughput"])
                file_size.append(iperf_data["file_size"])          
                groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', folder)
                distances.append(groups.group(5).split('m')[0])
        plot_dtime(key, distances, file_size, download_time)
        plot_throughput(key, distances, file_size, throughput)

for algorithm, spec in algo.items():
        plot_algo(algorithm, spec)
