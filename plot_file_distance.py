#!/usr/bin/python3.7

import os
import re
import numpy as np
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
from matplotlib import cm

def plot(fig, ax, figure_name, x, y, z, xlabel, ylabel, zlabel, folder_name):
        y = np.array(y)
        x = np.array(x)
        z = np.array(z)
    
        ax.plot_trisurf(x, y, z, color='yellow', antialiased=False, alpha=0.5, linewidth = 0.25)
        ax.set(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
                title=figure_name)
        fig.tight_layout()

        fig.savefig(f'{folder_name}/{figure_name}.png')

def plot_dtime(algo, distances, files_size, downloads_time, folder_name):
        fig = plt.figure(num=1, clear=True)
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.invert_xaxis()
        ax.azim = -40
        ax.dist = 10
        ax.elev = 20

        distances = [float(x) for x in distances]
        files_size = [float(x) for x in files_size]
        downloads_time = [float(x) for x in downloads_time]
        
        plot(fig, ax, f"{algo}_dtime", files_size, distances, downloads_time, "File Size[MB]", "Distance [m]", "Download time [s]", folder_name)

def plot_throughput(algo, distances, files_size, throughputs, folder_name):
        fig = plt.figure(num=1, clear=True)
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.azim = -40
        ax.dist = 10
        ax.elev = 20

        distances = [float(x) for x in distances]
        files_size = [float(x) for x in files_size]
        throughputs = [float(x) for x in throughputs]

        ax.set_ylim(max(distances), min(distances))
        plot(fig, ax, f"{algo}_throughput", files_size, distances, throughputs, "File Size[MB]", "Distance [m]", "Throughput [Mb/s]", folder_name)

def plot_algo(algo, results):
        download_time = []
        throughput = []
        distances = []
        file_size = []
        loss_rate = []

        for specific_algo, folders in results.items():
                for folder in folders:
                    iperf_data = extract_iperf_data(folder)
                    if iperf_data == None:
                        continue
                    download_time.append(iperf_data["time"])
                    throughput.append(iperf_data["throughput"])
                    file_size.append(iperf_data["file_size"])          
                    groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', folder)
                    distances.append(groups.group(5).split('m')[0])
                    with open(f"{folder}/results/{folder}.txt", "r+") as f:
                        lines = f.readlines()
                        num_pckt = str(lines[0]).split("=")[1]
                        ret = str(lines[1]).split("=")[1]
                        dup = str(lines[2]).split("=")[1]
                        los = str(lines[3]).split("=")[1]
                        print(f"{folder} loss = {los}, dup = {dup}, ret = {ret}")
                        loss_rate.append(int(dup)/int(num_pckt))


        throughputs = [float(x) for x in throughput]
        downloads_time = [float(x) for x in download_time]
        files_size = [float(x) for x in file_size]
        distances = [float(x) for x in distances]

        all_dist = []
        for dist in distances:
                if not dist in all_dist:        
                        all_dist.append(dist)

        all_fz = []
        for fz in files_size:
                if not fz in all_fz:
                        all_fz.append(fz)


        thr_fig, thr_ax = plt.subplots(2, 2, figsize=(10, 10), subplot_kw=dict(projection='3d'))

        for i in range(4):
                thr_ax[i // 2, i % 2].azim = -40
                thr_ax[i // 2, i % 2].dist = 10
                thr_ax[i // 2, i % 2].elev = 20
                thr_ax[i // 2, i % 2].set_xticks(all_fz)
                thr_ax[i // 2, i % 2].set_yticks(all_dist)
                thr_ax[i // 2, i % 2].set(xlabel="File Size[MB]", ylabel="Distance [m]", zlabel="Throughput [Mb/s]",
                           title=f"{algo} Throughput")

        dt_fig, dt_ax = plt.subplots(2, 2, figsize=(10, 10), subplot_kw=dict(projection='3d'))
 
        for i in range(4):
                dt_ax[i // 2, i % 2].azim = -40
                dt_ax[i // 2, i % 2].dist = 10
                dt_ax[i // 2, i % 2].elev = 20
                dt_ax[i // 2, i % 2].invert_xaxis()
                dt_ax[i // 2, i % 2].set_xticks(all_fz)
                dt_ax[i // 2, i % 2].set_yticks(all_dist)
                dt_ax[i // 2, i % 2].set(xlabel="File Size[MB]", ylabel="Distance [m]", zlabel="Download time [s]",
                          title=f"{algo} Download Time")

        loss_fig, loss_ax = plt.subplots(2, 2, figsize=(10, 10), subplot_kw=dict(projection='3d'))
 
        for i in range(4):
                loss_ax[i // 2, i % 2].azim = -40
                loss_ax[i // 2, i % 2].dist = 10
                loss_ax[i // 2, i % 2].elev = 20
                loss_ax[i // 2, i % 2].invert_xaxis()
                loss_ax[i // 2, i % 2].set_xticks(all_fz)
                loss_ax[i // 2, i % 2].set_yticks(all_dist)
                loss_ax[i // 2, i % 2].set(xlabel="File Size[MB]", ylabel="Distance [m]", zlabel="Packet Loss [%]",
                          title=f"{algo} Packet Loss")

        colors = ["yellow", "red", "blue", "black"]
        thr_cmap = ['gist_heat' for i in range(4)]
        dt_cmap = ['coolwarm' for i in range(4)]
        index = -1

        min_thr = min(throughputs)
        max_thr = max(throughputs)
        min_dt = min(downloads_time)
        max_dt = max(downloads_time)
        min_loss = int(min(loss_rate))
        max_loss = int(max(loss_rate))

        for specific_algo, folders in results.items():
                index += 1
                distances = []
                download_time = []
                throughput = []
                file_size = []
                loss_rate = []
                pckt_loss_file_name = ''
                for folder in folders:
                    iperf_data = extract_iperf_data(folder)
                    if iperf_data == None:
                        continue
                    download_time.append(iperf_data["time"])
                    throughput.append(iperf_data["throughput"])
                    file_size.append(iperf_data["file_size"])          
                    groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', folder)
                    distances.append(groups.group(5).split('m')[0])
                    pckt_loss_file_name = folder

                    with open(f"{folder}/results/{pckt_loss_file_name}.txt", "r+") as f:
                        lines = f.readlines()
                        num_pckt = str(lines[0]).split("=")[1]
                        ret = str(lines[1]).split("=")[1]
                        dup = str(lines[2]).split("=")[1]
                        los = str(lines[3]).split("=")[1]
                        loss_rate.append(int(dup)/int(num_pckt))

                distances = [float(x) for x in distances]
                files_size = [float(x) for x in file_size]
                throughputs = [float(x) for x in throughput]
                downloads_time = [float(x) for x in download_time]
                loss_rate = [float(x) for x in loss_rate]

                thr_ax[index // 2, index % 2].set_ylim(max(distances), min(distances))

                thr_ax[index // 2, index % 2].set_title(f"{specific_algo} Throughput", pad=5)
                dt_ax[index // 2, index % 2].set_title(f"{specific_algo} Download Time", pad=5)
                loss_ax[index // 2, index % 2].set_title(f"{specific_algo} Packet Loss", pad=5)

                distances = np.array(distances)
                files_size = np.array(files_size)
                throughputs = np.array(throughputs)
                downloads_time = np.array(downloads_time)
                loss_rate = np.array(loss_rate)

                if True: 
                        thr_ax[index // 2, index % 2].plot_trisurf(files_size, distances, throughputs, cmap=thr_cmap[index], antialiased=False, alpha=0.5, linewidth = 0.25, vmin = min_thr * 0.1, vmax = max_thr * 2)
                        dt_ax[index // 2, index % 2].plot_trisurf(files_size, distances, downloads_time, cmap=dt_cmap[index], antialiased=False, alpha=0.5, linewidth = 0.25, vmin = min_dt * 0.1, vmax = max_dt * 2)
                        loss_ax[index // 2, index % 2].plot_trisurf(files_size, distances, loss_rate, cmap=dt_cmap[index], antialiased=False, alpha=0.5, linewidth = 0.25, vmin = min_loss * 0.1, vmax = max_loss * 2)
                else:
                        thr_ax[index // 2, index % 2].plot_trisurf(files_size, distances, throughputs, color=colors[index], antialiased=False, alpha=0.5, linewidth = 0.25)
                        dt_ax[index // 2, index % 2].plot_trisurf(files_size, distances, downloads_time, color=colors[index], antialiased=False, alpha=0.5, linewidth = 0.25)
                        loss_ax[index // 2, index % 2].plot_trisurf(files_size, distances, loss_rate, color=colors[index], antialiased=False, alpha=0.5, linewidth = 0.25)

        thr_fig.tight_layout(rect=[0, 0.01, 0.98, 0.95])
        dt_fig.tight_layout(rect=[0, 0.01, 0.98, 0.95])
        loss_fig.tight_layout(rect=[0, 0.01, 0.98, 0.95])

        thr_fig.savefig(f'{algo}/{algo}_throughputs.png')
        
        dt_fig.savefig(f'{algo}/{algo}_dtime.png')

        loss_fig.savefig(f'{algo}/{algo}_pckt_loss.png')

not_c = []
def extract_iperf_data(folder):
        with open(f"{folder}/results/iperf.txt", "r") as f:      
                lines = f.readlines()
                if len(lines) == 0:
                        not_c.append(folder)
                        return None

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
                if iperf_data == None:
                        continue
                download_time.append(iperf_data["time"])
                throughput.append(iperf_data["throughput"])
                file_size.append(iperf_data["file_size"])          
                groups = re.search('([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z]*)_([a-zA-Z0-9]*)_([a-zA-Z0-9]*)', folder)
                distances.append(groups.group(5).split('m')[0])
        if not os.path.exists(f"{groups.group(1)}"):
                os.makedirs(f"{groups.group(1)}")

        plot_dtime(key, distances, file_size, download_time, groups.group(1))
        plot_throughput(key, distances, file_size, throughput, groups.group(1))

for algorithm, spec in algo.items():
        plot_algo(algorithm, spec)
print(not_c)
