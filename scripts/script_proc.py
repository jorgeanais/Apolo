import glob

import apolo.catalog_proc.crossproc
from apolo.catalog_proc import gaia_retrieval, utils, twomass_retrieval, preproc
import multiprocessing as mp
from apolo.data import objects, dirconfig

"""
This script summarize all the necessary steps to obtain final catalogs from the original data. 
    1. Proc VVV
    2. Download Gaia
    3. Proc Gaia
    4. Download 2MASS
    5. Proc 2MASS
    6. Proc combis
    7. VVV x 2MASS
    8. VVV x Gaia cleaning
    9. VVV x 2MASS x combis
   10. VVV x combis
   11.
"""

# Preliminars ----------------------------------------------
# Define where is the root of the data directory editing base_path variable in 'catalog_proc/dirconfig.py' file
# VVV and Combis catalogs are not public. Is expected that those files will be placed in their respective folders
# as follows:
#  - VVV PSF photometry ('*.cals') files should be in 'raw/vvv/' folder
#  - Combis ('*.csv') files should be in 'raw/combis/' folder

utils.check_base_data_structure()

# Number of parallel processes (it could be ram intensive)
# In my PC I have 6 cores available and 32 gb of ram
n_processes = mp.cpu_count() - 1

# Step 1
# Select sources that contain J, H and ks bands in VVV PSF catalogs (objects with missing values are omitted).
# It also adds and id, galactic coordinates and colors: H-Ks, J-Ks and J-H.

raw_vvv_files = glob.glob(dirconfig.raw_vvv + '/*.cals')
utils.make_dir(dirconfig.proc_vvv)

# parallel execution
with mp.Pool(n_processes-1) as pool:
    pool.map(preproc.process_vvv_cals, raw_vvv_files)

# Step 2
# Download gaia data. Before that you need
# You can edit data/objects.py file to add more tiles if needed. You must provide lmin, lmax, bmin, bmax values for
# each new tile.
# https://gea.esac.esa.int/archive/
# Each query takes ~10 min

utils.make_dir(dirconfig.raw_gaia)

with mp.Pool(n_processes) as pool:
    pool.map(gaia_retrieval.download_votable, objects.all_tiles.values())

# Step 3
# Pre-process gaia data to extract only features of interest and save to a fits file.
# Note: float missing values are filled by 1e20 (I dont know why), be careful!

raw_gaia_files = glob.glob(dirconfig.raw_gaia + '/*.vot.gz')
utils.make_dir(dirconfig.proc_gaia)

with mp.Pool(n_processes) as pool:
    pool.map(preproc.process_gaia_vot, raw_gaia_files)

# Step 4
# Download 2MASS catalog (only a selection of tiles, according to our new ROI definition)

selection_of_tiles = objects.tiles_in_roi

for tile in selection_of_tiles:
    print("Downloading: ", tile)
    twomass_retrieval.download_vot(tile)

# Step 5
# Pre-process 2MASS catalogs.
# It extract only AAA sources from 2mass catalog (including mag in VISTA system)

utils.make_dir(dirconfig.proc_2mass)
raw_2mass_files = glob.glob(dirconfig.raw_2mass + '/*.vot')

with mp.Pool(n_processes) as pool:
    pool.map(preproc.process_2mass_vot, raw_2mass_files)


# Step 6
# transform proper motion catalog in csv format into fits

pm_files = glob.glob(dirconfig.raw_combis + '/*.csv')

utils.make_dir(dirconfig.proc_combis)

with mp.Pool(n_processes) as pool:
    pool.map(preproc.process_combis_csv, pm_files)

# Step 7
# Clean the fits catalogs using parallax from gaia.
# Be careful here, files from config.proc_gaia_dir and config.proc_vvv_dir
# should match (that is why list are sorted first).
# utils.gaia_cleaning() will raise an error if 'TILE' key (metadata) are not equals.

files_vvv_gaia = utils.get_file_pairs(objects.tiles_in_roi, dirconfig.proc_vvv, dirconfig.proc_gaia)

utils.make_dir(dirconfig.cross_vvv_gaia)
utils.make_dir(dirconfig.cross_vvv_gaia_cont)

with mp.Pool(n_processes) as pool:
    pool.starmap(apolo.catalog_proc.crossproc.gaia_cleaning, files_vvv_gaia)


# Step 8
# generate a combined catalog from VVV and 2MASS

files_vvv_2mass = utils.get_file_pairs(objects.tiles_in_roi, dirconfig.proc_vvv, dirconfig.proc_2mass)
utils.make_dir(dirconfig.cross_vvv_2mass)

with mp.Pool(n_processes) as pool:
    pool.starmap(apolo.catalog_proc.crossproc.combine_vvv_2mass, files_vvv_2mass)

# Step 9
# Generate VVV x 2MASS x Combis

files_vvv2mass_combis = utils.get_file_pairs(objects.tiles_in_roi, dirconfig.cross_vvv_2mass, dirconfig.proc_combis)
utils.make_dir(dirconfig.cross_vvv2mass_combis)



# Step 10
# Todo: Generate VVV x 2MASS x Combis x Gaia
