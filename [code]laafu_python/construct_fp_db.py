"""
Construct fingerprint database with client data, using GPR
Converted from LIN Wenbin's C++ version

Author: Robert ZHAO Ziqi
"""

from test_gp import ap_map_rp, ap_map_rp_std, test_gp_all_ap
from utils import mkdir
import settings
import os.path

def separate(file_path, n):
    """Separate the original file into n parts

    Args:
        file_path (str): the path of the file to be separated, using os.path.join
        n (int): the number of partitions
    """

    paths_dir = os.path.splitext(file_path)[0]

    count = 0
    file_list = []

    with open(file_path, 'r') as f_in:
        for i in range(n):
            path_i = "{}{}.txt".format(paths_dir,i)
            f_out = open(path_i, 'w')
            file_list.append(f_out)
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            file_list[count].write(line+"\n")
            count = (count + 1) % n
        for f_out in file_list:
            f_out.close()

    print("Path file separated.")
        
def construct_fing(root_folder, loc_file_path, out_file_path, n, pre_dir, pre_res="res", pre_para="para"):
    """
    Construct fingerprint from files

    Args:
        client_folder(string):
        loc_file_path(string):
        out_file_path(string):
        n(int, default=4): the number of separated file 
        pre_dir(str, default="target"): prefix of the path files (targetX.txt by default)
        pre_res(str, default="res"): prefix of resulting folders (resX by default)
        pre_para(str, default="para"): prefix of GP paramter folders (paraX by default)
    """
    
    # step-1. for each direction (targetX.txt), process data using ApMapRp function.
    # Output values are stored in folder "targetX"
    for i in range(n):
        io_file = os.path.join(root_folder, "{}{}.txt".format(pre_dir, i))

        ap_map_rp(io_file)

    print("=========> Preprocess done!")

    # step-2. for each ap, run GP, simulate signal based on locations in locFile
    # Result is stored in folder "resX"
    for i in range(n):
        in_folder = os.path.join(root_folder, "{}{}".format(pre_dir,i))
        out_folder = os.path.join(root_folder, "{}{}".format(pre_res,i))
        para_folder = os.path.join(root_folder, "{}{}".format(pre_para,i))
        mkdir(out_folder)
        mkdir(para_folder)

        test_gp_all_ap(in_folder, loc_file_path, out_folder, para_folder)

    print("=========> GP Done!")

    # step-3. combine all into a file
    combine_fingerprint(root_folder, out_file_path, n, pre_res)

    print("=========> All done!")

def combine_fingerprint(in_folder_path, out_file_path, n, pre_res):
    """
    
    Args:
        in_folder_path(str):
        out_file_path(str):
        n(int, default=4): the number of separated file 
        pre_res(str, default="res"): prefix of resulting folders (resX by default)
        pre_para(str, default="para"): prefix of GP paramter folders (paraX by default)
    """

    with open(out_file_path, "w") as out_file:
        for i in range(n):
            loc_sig = {}
            sub_folder = os.path.join(in_folder_path, "{}{}".format(pre_res,i))
            ap_files = os.listdir(sub_folder)
            # load data for each AP
            for ap_file in ap_files:
                mac = os.path.splitext(ap_file)[0]
                # print(mac)
                with open(os.path.join(sub_folder, ap_file), "r") as in_file:
                    while True:
                        line = in_file.readline().rstrip("\n").rstrip(" ")
                        if not line:
                            break
                        # print(line)
                        [x, y, rssi] = line.split(" ")
                        loc_key = "{}-{}".format(x,y)
                        if loc_key not in loc_sig:
                            loc_sig[loc_key] = {}
                        loc_sig[loc_key][mac] = rssi
            
            # store data for each location
            for key in loc_sig.keys():
                [x, y] = key.split("-")
                mac_rssi_dict = loc_sig[key]
                out_file.write("{},{},{},0".format(x,y,i+1))
                for mac_key in mac_rssi_dict.keys():
                    rssi = mac_rssi_dict[mac_key]
                    out_file.write(" {}:{},0.0,0.0".format(mac_key,rssi))
                out_file.write("\n")

            loc_sig.clear()
                    
