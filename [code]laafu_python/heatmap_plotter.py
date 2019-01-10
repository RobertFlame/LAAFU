'''
This file is a plotting toolbox for visualizing the data
Author: Robert ZHAO Ziqi
'''

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from gaussian_process import gp
import os
import settings

const_sd = 3.0
const_step = 80

def extract_data(filename, scale):
    data_list = []
    with open(filename,'r') as f_in:
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            datum = line.split(" ")
            data_list.append(datum)
    mac = os.path.splitext(os.path.basename(filename))[0]
    position = np.array([[round(float(datum[0])),round(float(datum[1]))] for datum in data_list])
    rssi = np.array([float(datum[2]) for datum in data_list])
    if scale == True:
        position = settings.ptm_ratio * position
        position = np.round(position)
    return position, rssi, mac

def find_bounds(loc_file):
    x_bound = []
    y_bound = []
    with open(loc_file) as f_in:
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            x,y = line.split(" ")
            x = int(x)
            y = int(y)
            if len(x_bound) == 0:
                x_bound.append(x)
                x_bound.append(x)
            if len(y_bound) == 0:
                y_bound.append(y)
                y_bound.append(y)
            if x < x_bound[0]:
                x_bound[0] = x
            if x > x_bound[1]:
                x_bound[1] = x
            if y < y_bound[0]:
                y_bound[0] = y
            if y > y_bound[1]:
                y_bound[1] = y

    return x_bound[0],x_bound[1],y_bound[0],y_bound[1]

def plot_ap_heatmap(filename, root_path, mode, scale=False):
    position, rssi, mac = extract_data(filename, scale)
    loc_file = os.path.join(root_path, 'loc.txt')
    x_min, x_max, y_min, y_max = find_bounds(loc_file)

    x_edge = [int(item) for item in np.arange(x_min, x_max, (x_max-x_min)/const_step)]
    y_edge = [int(item) for item in np.arange(y_min, y_max, (y_max-y_min)/const_step)]
    xset, yset = np.meshgrid(x_edge, y_edge)

    gp_instance = gp(position,rssi)
    gp_instance.train()

    x_list = xset.ravel()
    y_list = yset.ravel()
    output = np.zeros(shape=(len(x_list)))
    err = np.zeros(shape=(len(x_list)))
    
    for idx in range(len(x_list)):
        out, e = gp_instance.estimate_gp(x_list[idx],y_list[idx],sd_mode=True)
        output[idx] = out
        err[idx] = e

    output,err = output.reshape(xset.shape),err.reshape(xset.shape)
    up,down = output+const_sd*err, output-const_sd*err
    
    if mode == '3d':
        fig = plt.figure(figsize=(5.5,5))
        ax1 = fig.add_subplot(111, projection='3d')
        ax1.plot_wireframe(xset,yset,output, linewidth=0.5, antialiased=True) # surface
        ax1.plot_wireframe(xset,yset,up,colors='lightgreen',linewidths=0.5, antialiased=True) # upper
        ax1.plot_wireframe(xset,yset,down,colors='lightgreen',linewidths=0.5, antialiased=True) # lower
        ax1.scatter(position[:,0],position[:,1],rssi,s=1,c='black')
        ax1.set_title('AP Heatmap: {}'.format(mac))
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('AP Signal Strength')
    
        plt.show()
    
    if mode == '2d':
        fig = plt.figure(figsize=(6,5))
        ax1 = fig.add_subplot(111)
        plot = ax1.pcolormesh(xset, yset, output)
        plt.colorbar(plot)
        ax1.set_title('AP Heatmap: {}'.format(mac))
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        plt.show()

def plot_ap_loc(root_path, n, pre_para="para"):
    x_loc = []
    y_loc = []
    mac_loc = []
    for idx in range(n):
        folder = os.path.join(root_path, "{}{}".format(pre_para,idx))
        for ap_para in os.listdir(folder):
            x_ap = 0
            y_ap = 0
            mac = os.path.splitext(ap_para)[0]
            with open (os.path.join(folder,ap_para),"r") as f_in:
                while True:
                    line = f_in.readline().rstrip("\n").rstrip(" ")
                    if not line:
                        break
                    if line.startswith("X_ap: "):
                        x_ap = int(settings.ptm_ratio * float(line.split(" ")[1]))
                    if line.startswith("Y_ap: "):
                        y_ap = int(settings.ptm_ratio * float(line.split(" ")[1]))
                        break
            x_loc.append(x_ap)
            y_loc.append(y_ap)
            mac_loc.append(mac)
    loc_file = os.path.join(root_path, "loc.txt")
    fig,ax = plt.subplots()
    ax.scatter(x_loc, y_loc, c="blue")
    # for idx in range(len(mac_loc)):
    #     ax.annotate(mac_loc[idx],(x_loc[idx],y_loc[idx]))
    plt.show()

def plot_alt_ap(ap_file_path, root_path):
    ap_file = os.path.basename(ap_file_path)
    ap_folder = os.path.dirname(ap_file_path)
    all_data_file = os.path.join(ap_folder,"all_{}".format(ap_file))
    xlist = []
    ylist = []
    elist = []
    with open(all_data_file, "r") as f_in:
        line = f_in.readline().rstrip("\n").rstrip(" ")
        x_ap, y_ap = line.split(" ")
        x_ap = int(x_ap)
        y_ap = int(y_ap)
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            point,error,std = line.split(" ")
            x,y = point.split(",")
            xlist.append(int(x))
            ylist.append(int(y))
            elist.append(float(error))
    
    fig, ax = plt.subplots()

    ax.scatter(xlist,ylist,c="blue")

    for idx in range(len(elist)):
        ax.annotate(int(elist[idx]),(xlist[idx],ylist[idx]))
    ax.scatter(x_ap,y_ap,c="green")
    ax.annotate("AP",(x_ap,y_ap))

    alt_x = []
    alt_y = []
    with open(ap_file_path,"r") as f_in:
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            x,y = line.split(" ")
            alt_x.append(int(x))
            alt_y.append(int(y))
    ax.scatter(alt_x,alt_y,c="red")

    plt.show()