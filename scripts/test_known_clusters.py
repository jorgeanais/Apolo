from apolo.catalog_proc import utils
from apolo.test_tools.routines import clustering_routine
from apolo.test_tools.utils import which_tile
from apolo.data import dirconfig, objects
import multiprocessing as mp

"""
This script shows how I perform a 'clustering', according to our current methodology, to a 
set of know regions where I far-end-stellar-cluster is located.
This is done in parallel, this mean one process for each stellar-cluster region.
At the end you should find plots and files in your output folder for each stellar-cluster.
"""

utils.check_base_data_structure()

# First, define a list of cluster. If you want to add a new cluster object,
# you can do it in apolo/data/object.py. Then, which tile function will
# search their corresponding tile automatically.
clusters = [objects.m81, objects.cl86, objects.cl74, objects.cl88]
tiles = which_tile(clusters, objects.all_tiles)

# Define which parameter space do you want to use from the available presets: `Phot+PM` or `PhotOnly`
space_param = 'Phot+PM'

# Select which set of parameter do you want to use. Check apolo/data/dirconfig to have a complete list. For example
# - dirconfig.proc_vvv (only Javier photometry, do not include proper motions)
# - dirconfig.cross_vvv_gaia (only Javier photometry but cleaned used gaia)
# - dirconfig.cross_vvv_combis_gaia (This set includes Javier's photometry, pm from combis and cleaned using gaia)
# - dirconfig.cross_vvv_2mass_combis_gaia (This set includes vvv extended with 2mass, pm and cleaned using gaia)
data_dir = dirconfig.cross_vvv_2mass_combis_gaia

# This line setup the arguments for function clustering routine
models = [(cl, tile, space_param, data_dir) for cl, tile in zip(clusters, tiles)]

# Computation in parallel. Here we are calling clustering_routine function (in polo/clustering/ctools/ directory)
# and passing the arguments `models`,
with mp.Pool(mp.cpu_count() - 1) as pool:
    results = pool.starmap(clustering_routine, models)
