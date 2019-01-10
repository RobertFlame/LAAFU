import os
import numpy as np

def mkdir(path):
 
	folder = os.path.exists(path)
 
	if not folder:                  
		os.makedirs(path)            
		# print("---  new folder...  ---")
		# print("---  OK  ---")
 
	else:
		# print("---  Already have this folder!  ---")
		pass

def sqd_exp(sigma_f, l, sqd_sum_v):
    return (sigma_f**2) * (np.e**(-0.5 * sqd_sum_v / (l**2)))


def sqd_sum(x1, y1, x2, y2):
    return (x1 - x2)**2 + (y1 - y2)**2