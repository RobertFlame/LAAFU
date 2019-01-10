# This is a demo program for LAAFU with gaussian process and compressive sensing.
# Most of the parts are converted from LIN Wenbin's C++ version. Hope this python
# version is easier to use, develop and maintain.
#
# Author: Robert ZHAO Ziqi

# import compressive_sensing
from construct_fp_db import construct_fing, separate
from find_altered_ap import detect_alt_at_rp, merge_targets
from gaussian_process import gp
from test_gp import get_loc
from heatmap_plotter import plot_ap_heatmap
import settings

import utils
import os.path

def construct_fp_database(root_path,pre_paths, n=settings.separate_parts):
    pre_loc="loc"
    path_all = os.path.join(root_path,"{}.txt".format(pre_paths))
    path_rp = os.path.join(root_path, "db.txt")
    path_loc = os.path.join(root_path,"{}.txt".format(pre_loc))

    get_loc(path_all,loc_name=pre_loc)
    separate(path_all,n)
    construct_fing(root_path,path_loc,path_rp, n, pre_paths)


def detect(target, path):
    output = "{}_merge.txt".format(os.path.splitext(target)[0])
    merge_targets(target,output)
    rp_file = os.path.join(path,"db.txt")
    alter_path = os.path.join(os.path.dirname(target),"output_{}".format(os.path.basename(os.path.splitext(target)[0])))
    detect_alt_at_rp(target,rp_file,alter_path)

def detect_original(target, path):
    rp_file = os.path.join(path,"db.txt")
    alter_path = os.path.join(os.path.dirname(target),"output_{}".format(os.path.basename(os.path.splitext(target)[0])))
    detect_alt_at_rp(target,rp_file,alter_path)

