"""
Apr 14, 2020
Christopher Fichtlscherer (fichtlscherer@mailbox.org)
GNU General Public License

Douglas-Rachford-Verfahren (Classon Skript p.69)
"""

import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt
from tqdm import tqdm
import time as time

from ktra.k_transform import create_source_point_d
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



def inner_of_box(x, y, z):
    """ Different shells around the origin."""

    rad_pos = (x**2 + y**2 + z**2)**0.5
    
    if rad_pos <= 0.3: return 0.0
    if rad_pos <= 0.7: return 0.0
    if rad_pos <= 0.9: return 0.8
   
    return 0

def rof_function(approx, signal, reg):                                       
    """the functional I want to minimize"""                                  
                                                                             
    norm_term = np.linalg.norm(signal-approx)**2                             
                                                                             
    tv_term = np.sum(np.abs((reg * approx - np.roll(reg * approx, -1))[:-1]))
                                                                             
    punish = 0.5 * norm_term + tv_term                                       
                                                                             
    return punish                                                            


def count_edges_for_reg(dist, dist_array):
    """ this function will return a vector according to the different distances
    in a threed model and returns a vector which indicates how many voxels have
    this distance. This is used for the vector regularisation parameter"""

    dist_count_array = np.ones(dist_array.size)

    dist_r = np.round(dist, 6)

    for i in range(dist_array.size):
        dist_count_array[i] = np.sum(dist_r == dist_array[i])
    
    return dist_count_array
    


def y_function(values_1d, *args):                                       
    """the function we are optimizing - y = values_1d"""                                     
                                                                             
    liam_all, cont_results, gamma, x, z = args         

    value_results = k_trafo_one_dim_all(liam_all, values_1d)                 
    value_difference_norm = np.linalg.norm(value_results - cont_results)**2  
    
    difference = np.linalg.norm(2*x - z - values_1d)**2                                
    
    y =  0.5 * difference + 0.5 * gamma * value_difference_norm
    
    return y


def x_step(x, y, z, alpha, gamma):
    
    approx = x

    x = scipy.optimize.minimize(rof_function, approx, args = (z, reg*gamma))

    return x.x


def y_step(x, z, y, gamma, liam_all, cont_results_noise):

    y = scipy.optimize.minimize(y_function,
                                y,
                                args = (liam_all, cont_results_noise, gamma, x, z),
                                method = 'L-BFGS-B',
                                bounds = scipy.optimize.Bounds(0, 1),
                                options = {'disp': False})
                                #           'maxcor': 10,
                                #           'ftol': 10**-20,
                                #           'gtol': 10**-20,
                                #           'eps': 10**-8, # if to high stops fast
                                #           'maxiter': 10**7,
                                #           'maxls': 100,
                                #           'maxfun': 10**7})
    
    return y.x


def z_step(x, y, z):

    z = z + y - x
    
    return z


steps = 5

cuboid_coordinates = {'x1': -1, 'x2': 1, 'y1': -1, 'y2': 1, 'z1': -1, 'z2': 1}

x_cor, y_cor, z_cor = coordinate_discretization(cuboid_coordinates, steps)
dist = distance_creater(x_cor, y_cor, z_cor, steps)
dist_array = dist_array_maker(dist)
dist_count_array = count_edges_for_reg(dist, dist_array)

different_lengths = len(dist_array)

number_ktrans = int(different_lengths*10)
number_rays = {'dim_1': 5, 'dim_2': 5}
fineness = 10**3

radii = np.linspace(2,30, different_lengths) #[2.1, 2.3, 2.5, 2.7, 2.9, 3.1, 3.3, 3.5]

start_index = [i * int(number_ktrans / len(radii)) for i in range(len(radii))]
end_index = [i * int(number_ktrans / len(radii)) for i in range(1, len(radii) + 1)]

source_point_d = {}

################################################################################
for i, r in enumerate(radii):
    new_source_points = create_source_point_d(r, end_index[i], perc_circle=0.125, start_index=start_index[i])
    source_point_d.update(new_source_points)

number_ktrans = len(source_point_d) 
print("1/8")

rays_d = generate_rays_d(source_point_d, cuboid_coordinates, number_rays)
print("2/8")

if True:
    liam_all = generate_all_line_integral_array_matrix(rays_d, cuboid_coordinates, steps, fineness)
    np.save("liam_all", liam_all)
    print("3/8")

if True:
    cont_results = create_con_results(rays_d, inner_of_box, fineness)
    np.save("cont_results", cont_results)
print("4/8")

#compare_values = compare_values_original_function(cuboid_coordinates, steps, inner_of_box)
print("5/8")

x_cor, y_cor, z_cor = coordinate_discretization(cuboid_coordinates, steps)
print("6/8")

values = discretization_of_model(x_cor, y_cor, z_cor, inner_of_box, steps)
print("7/8")

x = 0.5 * np.ones(different_lengths)
y = 0.5 * np.ones(different_lengths)
z = 0.5 * np.ones(different_lengths)

reg = dist_count_array * 0.003
gamma = 25 
perc_noise = 0

cont_results = np.load("cont_results.npy")  
liam_all = np.load("liam_all.npy")

discrete_model = discretization_of_model(x_cor, y_cor, z_cor, inner_of_box, steps)             
one_d_model = threed_to_oned(discrete_model, cuboid_coordinates, steps)
#dis_results = k_trafo_one_dim_all(liam_all, one_d_model)                                       
print("8/8")
v1d = threed_to_oned(values, cuboid_coordinates, steps)

cont_results_noise = cont_results + perc_noise * np.max(cont_results) * 2 * (np.random.random(number_ktrans) - 0.5)


################################################################################
####################### Make wD data for comparing##############################
################################################################################

x_comp = np.arange(-1, 1, 0.01)                  
y_comp = np.arange(-1, 1, 0.01)                  
                                            
cont = np.zeros((x_comp.size, y_comp.size))           
                                            
for i in range(x_comp.size):                     
    for j in range(y_comp.size):                 
        cont[i,j] = inner_of_box(x_comp[i], y_comp[j], 0)


################################################################################

for i in range(5000):
    
    x_old, y_old, z_old = x, y, z

    x = x_step(x, y, z, reg, gamma)
    y = y_step(x, z, y, gamma, liam_all, cont_results_noise)
    z = z_step(x, y, z)
    
    print(i, "--------", np.linalg.norm(x - x_old))
    
    if i % 25==0:
        results3d = make_threed_back(x, steps, cuboid_coordinates)
    
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(7,3.5))
        ax[0].imshow(cont, vmin=0, vmax=1.2)                     
        ax[0].axis(False)          
        ax[1].imshow(results3d[int(steps/2)], vmin=0, vmax=1.2)             
        ax[1].axis(False)                                        
        plt.savefig(str(i) + ".png")
        plt.close()
        np.save("x_" + str(i), x)


#    if i % 10 == 0:
#        plt.plot(v1d, "-o")
#        plt.plot(x, "-o")
#        plt.grid(True)
#        plt.savefig(str(i) + ".png")
#        plt.close()
#        np.save("x_" + str(i), x)
