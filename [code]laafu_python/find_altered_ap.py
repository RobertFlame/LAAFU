"""
Detect altered APs at RPs, using GPR
Converted from LIN Wenbin's C++ version

Author: Robert ZHAO Ziqi
"""

from gaussian_process import gp
from test_gp import ap_map_rp, ap_map_rp_std
from utils import mkdir, sqd_exp, sqd_sum
import settings

import numpy as np
import os.path

def merge_targets(in_file_path, out_file_path):
    """
    
    Args:
        in_file_path(str):
        out_file_path(str):
    """

    mac_rssis = {} # one mac correspond to a list of rssis
    index = 0

    with open(in_file_path, 'r') as f_in, open(out_file_path, 'w') as f_out:
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            # get the first item of line (x,y,dir,id)
            location_info = line.split(" ")[0]
            # discard the first item for each line
            # (mac:rssi,std,freq)?
            for mac_rssi_pair in line.split(" ")[1:]:
                mac,rssi = mac_rssi_pair.split(",")[0].split(":")
                # Store the pair in the dict
                if mac not in mac_rssis:
                    mac_rssis[mac] = []
                mac_rssis[mac].append(rssi)
            index += 1
            if (index==5):
                # Do this every 5 readings
                # create the output string
                output_str = location_info
                # compute the mean signal value and add it to the output string
                for mac_add in mac_rssis.keys():
                    rssi_list = mac_rssis[mac_add]
                    if len(rssi_list) == 0:
                        mean_signal = 0
                    else:
                        count = 0
                        total = 0
                        for rssi in rssi_list:
                            total += int(rssi)
                            count += 1
                        mean_signal = float(total / count)
                    output_str += " {}:{},0.0,1.0".format(mac_add,mean_signal)
                # write the output stirng to the file
                f_out.write(output_str + "\n")
                # clear the dict and reset index
                mac_rssis.clear()
                index = 0
                

def detect_alt_at_rp(target_file, rp_file, out_folder):
    """
    
    Args:
        client_file(str):
        rp_file(str):
        out_folder(str):
    """
    
    n_sigma = settings.n_sigma
    interval =  settings.interval # grid size in pixels
    min_length = settings.min_length  # minimum length of series to be processed
    neighbour_bound = settings.neighbour_bound  # minimum count of neighbour to be counted as altered

    interval_square = interval ** 2

    ap_map_rp(target_file)  # Measured in meters
    ap_map_rp_std(rp_file)  # Measured in pixels

    # print("Finished preprocessing")

    rp_folder = os.path.splitext(rp_file)[0]
    mkdir(out_folder)

    target_folder = os.path.splitext(target_file)[0] # files in client folder
    # for each AP file in client data
    for ap_file in os.listdir(target_folder):
        pos_train = []
        rssi_train = []
        # run GP for each AP using client data
        with open(os.path.join(target_folder,ap_file), 'r') as f_in:
            # load (x y rssi) for each file
            while True:
                line = f_in.readline().rstrip("\n").rstrip(" ")
                if not line:
                    break
                tx, ty, trssi = line.split(" ")
                pos_train.append([tx,ty])
                rssi_train.append(trssi)

        # Discard series with short length
        if (len(rssi_train) <= min_length):
            continue
        
        gp_instance = gp(pos_train, rssi_train)
        gp_instance.train()

        # load RP data with same AP mac
        x = 0
        y = 0
        rp_pos = []
        rp_rssi = []
        total_var  = 0.0
        n_var = 0

        rp_ap_file = os.path.join(rp_folder,ap_file)
        if not os.path.exists(rp_ap_file):
            continue
        with open(rp_ap_file, 'r') as f_in: 
            # load (x y rssi sd)
            while True:
                line = f_in.readline().rstrip("\n").rstrip(" ")
                if not line:
                    break
                x,y,rssi,sd = line.split(" ")
                x = int(float(x))
                y = int(float(y))
                rssi = float(rssi)
                sd = float(sd)
                rp_pos.append([x,y])
                rp_rssi.append(rssi)
                if sd > 0.0:
                    total_var += sd ** 2
                    n_var += 1
        # compute the shared mean standard deviation
        if n_var == 0:
            mean_var = 0.0
        else:    
            mean_var = float(total_var / n_var)

        # test at each rp for one ap
        all_err_file = os.path.join(out_folder,"all_{}".format(ap_file))
        pos = []
        with open(all_err_file, "w") as f_out:
            para = gp_instance.parameters()
            x_ap = int(float(para[2])*settings.ptm_ratio)
            y_ap = int(float(para[3])*settings.ptm_ratio)
            f_out.write("{} {}\n".format(x_ap,y_ap))
            for j in range(len(rp_pos)):
                dx = rp_pos[j][0] / settings.ptm_ratio     # Convert to meters
                dy = rp_pos[j][1] / settings.ptm_ratio

                e_rss, e_sd = gp_instance.estimate_gp(dx,dy,sd_mode=True)

                if e_rss < settings.min_rssi:
                    e_rss = settings.min_rssi
                
                diff = float(rp_rssi[j] - e_rss)
                temp_sd = np.sqrt(mean_var + e_sd**2)
                f_out.write("{},{} {} {}\n".format(rp_pos[j][0], rp_pos[j][1], diff, float(temp_sd)))
                if abs(diff) > temp_sd * n_sigma:
                    pos.append([rp_pos[j][0],rp_pos[j][1]]) # Altered at this rp
        
        # ----- half-neighbour filtering
        out_str = ""
        for j in range(len(pos)):
            rx = pos[j][0]
            ry = pos[j][1]

            neighbour = -1  # ignore the point itself
            # count neighbour
            for point in rp_pos:
                dist_sq = sqd_sum(rx,ry,point[0],point[1])
                if dist_sq < interval_square:
                    neighbour += 1  

            al_neighbour = 0
            # count how many neighbour is altered
            for k in range(len(pos)):
                if k == j: # ignore the point itself
                    continue
                rx1 = pos[k][0]
                ry1 = pos[k][1]
                dist_sq = sqd_sum(rx,ry,rx1,ry1)
                if dist_sq < interval_square:
                    # print("{}:{}".format(dist_sq,interval_square))
                    al_neighbour += 1

            # only when more than half neighbours altered
            if al_neighbour * 2 >neighbour and neighbour > neighbour_bound:
                out_str += "{} {} \n".format(rx, ry)
        if out_str != "":
            out_file = os.path.join(out_folder,ap_file)
            with open(out_file,'w') as f_out:
                f_out.write(out_str)
            
