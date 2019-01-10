'''
This file will store some of the paramters of the whole LAAFU program
Author: Robert ZHAO Ziqi
'''

# This controls when to discard AP with small number of corresponding positions
# Used in ap_map_rp() in test_gp.py
min_size_to_process = 5 

# This controls how many parts will the data be divided into
# Used in construct_fp_database() in main.py
separate_parts = 4

# This determines whether to consider z value of AP's location or not
# Used in constructor of GP
with_z = 1

# This is the conversion ratio from pixel to meter
# Used in test_gp.py
ptm_ratio = 13.3

# This is used for tolerance of alternation
# Used in find_altered_ap.py
n_sigma = 7

# This is used for half heighbour filtering interval
# Used in find_altered_ap.py
interval = 65

# minimum length of series to be processed
# Used in find_altered_ap.py
min_length = 15

# This is used for half neighbour filtering minimum count of neighbour to be counted as altered
# Used in find_altered_ap.py
neighbour_bound = 3

# Minimum value of RSSI
# Used in find_altered_ap.py
min_rssi = -100.0