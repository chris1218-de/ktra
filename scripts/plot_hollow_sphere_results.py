"""
Jul 10, 2020
Christopher Fichtlscherer (fichtlscherer@mailbox.org)
GNU General Public License

In this plot the 
"""

import matplotlib
import scipy.optimize
import numpy as np
import matplotlib.pyplot as plt

import time as time

from ktra.k_transform import create_rays
from ktra.k_transform import generate_rays_d                                
from ktra.k_transform import generate_all_line_integral_array_matrix        
from ktra.k_transform import coordinate_discretization                      
from ktra.k_transform import discretization_of_model                        
from ktra.k_transform import k_trafo_one_dim_all                            
from ktra.k_transform import create_line_matrix                             
                                                                            
from ktra.k_transform import distance_creater                               
from ktra.k_transform import dist_array_maker                               
                                                                            
from ktra.tv_denoising_condat import tv_denoising_algorithm                 
                                                                            
from ktra.optimization_process import create_con_results                    
from ktra.optimization_process import compare_values_original_function      
from ktra.optimization_process import important_mini_cuboids                
from ktra.optimization_process import threed_to_oned                        
from ktra.optimization_process import v_step_function                       
from ktra.optimization_process import how_many_got_hit                      
from ktra.optimization_process import generate_everything                   
from ktra.optimization_process import make_threed_back                      
                                                                            
from ktra.optimization_process import line_integral_cont



matplotlib.use("pgf")           
matplotlib.rcParams.update({    
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',     
    'text.usetex': True,        
    'pgf.rcfonts': False,       
})                              

figures_path = '/home/cpf/Desktop/k_transform_tomography/figures/'

#################### Plot the continuous_object ################################################

def inner_of_box(x, y, z):                     
    """ Different shells around the origin.""" 
                                               
    rad_pos = (x**2 + y**2 + z**2)**0.5        
                                               
    if rad_pos <= 0.3: return 0.0              
    if rad_pos <= 0.7: return 0.0              
    if rad_pos <= 0.9: return 0.9              
                                               
    return 0                                   

x_comp = np.arange(-1, 1, 0.01)                                
y_comp = np.arange(-1, 1, 0.01)                                
                                                               
cont = np.zeros((x_comp.size, y_comp.size))                    
                                                               
for i in range(x_comp.size):                                   
    for j in range(y_comp.size):                               
        cont[i,j] = inner_of_box(x_comp[i], y_comp[j], 0)      

plt.figure(figsize=(3,3))
plt.imshow(cont, vmin=0, vmax=1)
plt.axis(False)
plt.savefig(figures_path + 'hollow_sphere_cont.pgf', bbox_inches='tight')

#################### Plot the reconstruction from an npy file object #############################

data = np.load("hollow_sphere_reconstruction_results.npy")

cuboid_coordinates = {'x1': -1, 'x2': 1, 'y1': -1, 'y2': 1, 'z1': -1, 'z2': 1}
steps = 16

results3d = make_threed_back(data, steps, cuboid_coordinates)

plt.figure(figsize=(3,3))
plt.imshow(results3d[int(steps/2)], vmin=0, vmax=1)
plt.axis(False)
plt.savefig(figures_path + 'hollow_sphere_reconstruction.pgf', bbox_inches='tight')









