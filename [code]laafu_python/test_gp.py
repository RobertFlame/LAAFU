"""
For testing, implementation
Converted from LIN Wenbin's C++ version

Author: Robert ZHAO Ziqi
"""

from gaussian_process import gp
from utils import mkdir 
import os.path
import settings

# ######################## GP ########################

# -----------------------Prepare ---------------------

def ap_map_rp(file_path):
    """
    Args:
        file_path (str):
    """
    min_size_to_process = settings.min_size_to_process # change this to fit the data

    with open(file_path, 'r') as p_file:
        ap_rf = {}  # mac->{(x,y)->rssi}

        while True:
            line = p_file.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            # first record of each line. x,y,direction,id
            info = line.split(" ")[0]
            # convert pixel into meter 
            x = float(info.split(",")[0]) / settings.ptm_ratio
            y = float(info.split(",")[1]) / settings.ptm_ratio
            mac_rssi_list = line.split(" ")[1:]
            for mac_rssi in mac_rssi_list:
                # mac:rssi,std,freq
                mac = mac_rssi.split(":")[0]
                rssi = mac_rssi.split(":")[1].split(",")[0]
                if mac not in ap_rf:
                    ap_rf[mac] = {}
                ap_rf[mac]["{}-{}".format(x,y)] = float(rssi)

    # ignore those APs with too few data
    delete_list = []
    for mac_key in ap_rf.keys():
        if len(ap_rf[mac_key]) < min_size_to_process:
            delete_list.append(mac_key)
    for key in delete_list:
        del ap_rf[key]

    # use filename as a new folder
    io_dir = os.path.splitext(file_path)[0]
    mkdir(io_dir)

    for mac_key in ap_rf.keys():
        # use AP's mac address as a file name
        io_file = os.path.join(io_dir, "{}.txt".format(mac_key))
        with open(io_file, 'w') as out_file: 
            for pos_key in ap_rf[mac_key].keys():
                [x,y] = pos_key.split("-")
                rssi = ap_rf[mac_key][pos_key]
                out_file.write("{} {} {}\n".format(x,y,rssi))

def ap_map_rp_std(file_path):
    """
    Args:
        file_path (str):
    """

    with open(file_path, 'r') as p_file:
        ap_rf = {}

        while True:
            line = p_file.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            # first record of each line. x,y,direction,id
            info = line.split(" ")[0]
            x = float(info.split(",")[0])
            y = float(info.split(",")[1])
            mac_rssi_list = line.split(" ")[1:]
            for mac_rssi in mac_rssi_list:
                # mac:rssi,std,freq
                mac = mac_rssi.split(":")[0]
                rssi = float(mac_rssi.split(":")[1].split(",")[0])
                std = float(mac_rssi.split(":")[1].split(",")[1])
                if mac not in ap_rf:
                    ap_rf[mac] = {}
                ap_rf[mac]["{}-{}".format(x,y)] = [rssi, std]

    # use filename as a new folder
    io_dir = file_path.rstrip(".txt")
    mkdir(io_dir)

    for mac_key in ap_rf.keys():
        # use AP's mac address as a file name
        io_file = os.path.join(io_dir, "{}.txt".format(mac_key))
        with open(io_file, 'w') as out_file: 
            for pos_key in ap_rf[mac_key].keys():
                [x,y] = pos_key.split("-")
                [rssi,std] = ap_rf[mac_key][pos_key]
                out_file.write("{} {} {} {}\n".format(x,y,rssi,std))


# ------------------------Run-------------------------

def test_gp_all_ap(in_folder, loc_file_path, out_folder, para_folder):
    """
    
    Args:
        in_folder(str):
        loc_file_path(str):
        out_folder(str):
        para_folder(str):
    """
    in_files = os.listdir(in_folder)
    for in_file in in_files:
        # print out AP's mac address
        print("-----{}".format(in_file))

        pos_train = []
        rssi_train = []

        # load data
        with open(os.path.join(in_folder,in_file), 'r') as f_in:
            while True:
                line = f_in.readline().rstrip("\n").rstrip(" ")
                if not line:
                    break
                [x,y,rssi] = line.split(" ")
                pos_train.append([float(x), float(y)])
                rssi_train.append(float(rssi))

        # start training
        gp_instance = gp(pos_train, rssi_train)
        gp_instance.train()
        para_list = gp_instance.parameters()

        # output parameter file
        para_file = os.path.join(para_folder,in_file)
        field = ["A","B","X_ap","Y_ap","Z_ap","sigma_n","sigma_f","l"]
        with open(para_file, 'w') as f_out:
            for idx in range(len(field)):
                if idx == 4 and len(para_list) != 8:
                    continue
                if idx > 4 and len(para_list) != 8:
                    f_out.write("{}: {}\n".format(field[idx],para_list[idx-1]))
                else:
                    f_out.write("{}: {}\n".format(field[idx],para_list[idx]))

        # create output file in output folder
        out_file = os.path.join(out_folder, in_file)
        with open(out_file, 'w') as f_out, open(loc_file_path, 'r') as f_in:
            while True:
                # predict signal at RPs and save
                line = f_in.readline().rstrip("\n").rstrip(" ")
                if not line:
                    break
                [ix,iy] = line.split(" ")
                x = float(ix) / settings.ptm_ratio 
                y = float(iy) / settings.ptm_ratio

                [esti_rssi,esti_err] = gp_instance.estimate_gp(x,y,sd_mode=False)
                # print(esti_rssi)
                if esti_rssi< settings.min_rssi:
                    continue
                f_out.write("{} {} {}\n".format(ix, iy, esti_rssi))


# ################## Data Process #####################

def get_loc(file_path, loc_name="loc"):
    """
    Args:
        file_path(str):
        loc_name(str, default="loc): 
    """
    loc_file = os.path.join(os.path.dirname(file_path), "{}.txt".format(loc_name))
    val_list = []
    with open(file_path, 'r') as f_in, open(loc_file, 'w') as f_out:
        while True:
            line = f_in.readline().rstrip("\n").rstrip(" ")
            if not line:
                break
            x = int(line.split(" ")[0].split(",")[0])
            y = int(line.split(" ")[0].split(",")[1])
            if [x,y] not in val_list:
                val_list.append([x,y])
                f_out.write("{} {}\n".format(x,y))

    print("Location file generated.")
