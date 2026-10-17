#!/usr/bin/env python
# coding: utf-8

# # tobac with detection on Tb - tryout for paralell
# - what this nbook does:
#     - Nasa tb, IMERG and CCIC loaded, clip to tropics, resampled to IMERG grid
#     - tobac application:
#         - anvils 
#             - detect on Tb (Nasa-Tb)
#             - segmentate on Tb 
#             - bulk stats of IWP (CCIC)
#             - bulk stats on tb
#             - additional stats (area)
#             - save the mask (potenially features)
#         - precip cells
#             - detect on precip
#             - segmentate on precip
#             - bulk stats of Precip (precip)
#             - additional stats (area)
#             - save the mask (potenially features)
#         - merge anvil properties to cell features table to df_cell_combined
#         - add additional columns
#         - save df_cell_combined
#         - some plots to evaluate anvil and precip cell segmentation
# 
# - input:
#     - Nasa Tb, Imerg, CCIC 
#     - date YYYY-MM-DD-HHMM
# - adapt:
#     - output dir for seg results data
#     - tobac parameters for detection and segmentation
#     - date
# - output: (saving cells are set to raw => only executed if run with runner)
#     - Segmentation mask '{savedir}/features_{date}.h5'
#     - segmentation features (see note above) 'features_segmentation_inkl_bulkstats_{date}.nc'
#     - combined precip freatures df with anvil properties and further columns (FINAL PRODUCT)
# 

# In[1]:


import warnings

# ignore general categories
for cat in [FutureWarning, RuntimeWarning, UserWarning]:
    warnings.filterwarnings("ignore", category=cat)

# ignore specific repeated messages
for msg in [
    "pyproj unable to set PROJ database path",
    "As of v1.6.0, segmentation with time length 1",
    "Using DEFAULT_SPHERICAL_EARTH_RADIUS"
]:
    warnings.filterwarnings("ignore", message=msg)


# In[2]:


import numpy as np
import xarray as xr
import os

from pathlib import Path

# Import tobac itself:
import tobac
import tobac.utils

print("using tobac version", str(tobac.__version__))

import iris

# plotting
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import seaborn as sns

# load tools
import sys 
sys.path.append("../tools")
import handle_OBS_data

from defs_application import georegions 
import use_tobac
import plots_mapping


# In[3]:


os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"


# # arguments

# In[4]:


# set date
#date = "2020-06-06-2100"
#date = sys.argv[1]

# manual adaption for launcher if outputs shoul db

# threshold_anvils
detection_threshold_anvil = 225 # K, needs to be part of multi_detection_thresholds_anvil
multi_detection_thresholds_anvil = [225] #[210,215, 225, 230, 235, 241] # K # = detection_threshold_anvil
segmentation_threshold_anvil = 241 # K 235 # bolot 235, feng MCSIMP =< 240, Senf 230

# threhold precip
detection_threshold_cell = 10
multi_detection_thresholds_cell = [10] #[1,2,3,5,10] # mm/h # brueck 2020 => string convective features => detection high, to segmentate cell => lower threshold
segmentation_threshold_cell = 10# 0.1 brueck 2020. 10 senf

# build a descriptive tag from your parameters

param_tag = f"anvil_detectthres{detection_threshold_anvil}_seg{segmentation_threshold_anvil}_cell_detectthres{detection_threshold_cell}_seg{segmentation_threshold_cell}"
#param_tag



if "launcher" in sys.argv[0]: 
    date = "2023-12-01-1800"
    interactive =True
    saveoutputs = False
    savedir = Path("../output/apply_seg/apply_OBS_with_mask_from_nbook") # second_tune_OBS tobactryoutsdata_OBS
    interactive =False
    
else: 
    date = sys.argv[1]
    interactive = False
    saveoutputs = True
    savedir = Path("../output/apply_seg_new/apply_OBS") / param_tag # second_tune_OBS tobactryoutsdata_OBS
print(date)


# In[5]:


############# ANVILS ############
# detection para (Tb)
feature_detection_params_anvil = dict()
feature_detection_params_anvil["threshold"] = multi_detection_thresholds_anvil
feature_detection_params_anvil["target"] = "minimum"
feature_detection_params_anvil["position_threshold"] = "weighted_diff"
feature_detection_params_anvil["PBC_flag"]='hdim_2'

# Gaussian smoothing before detection
feature_detection_params_anvil["sigma_threshold"] =  0.5 # default 0.5

# from below 
dX = 11119.492664455873
dxy =  dX 
# minimum number of pixels below threshold_anvil
#feature_detection_params_anvil["n_min_threshold"] = 3 # one pixel approx 10km * 10km = 100km2

# minimum pixel distance to next feature
feature_detection_params_anvil["min_distance"]= dxy*20  # mcs ICON trakcing example *4 => aber wir haben geresamplet zu 11 x 11km 


# In[6]:


############# CELLS ############

# detection para (Tb)
feature_detection_params_cell = dict()
feature_detection_params_cell["threshold"] = multi_detection_thresholds_cell
feature_detection_params_cell["target"] = "maximum"
feature_detection_params_cell["position_threshold"] = "weighted_diff"
feature_detection_params_cell["PBC_flag"]='hdim_2'



# Gaussian smoothing before detection
feature_detection_params_cell["sigma_threshold"] = 0.05  
#feature_detection_params_cell["n_min_threshold"] = 3 # brueck


# In[7]:


# create main directory
savedir.mkdir(parents=True, exist_ok=True)

# define subdirectories
subdirs = [
    #"cell_features",
    # "anvil_features",
    "cell_features_combined",
    # "combi_mask",
    # "plots"
]

# create all subdirectories
for sub in subdirs:
    (savedir / sub).mkdir(parents=True, exist_ok=True)

# # plots dir
# plots_dir = savedir / "plots"


# # load data
# - load tb, precip, iwp
# - crop to tropical belt, allign coordiate logic
# - resmaple to imerg data so everything has same resolution (for bulk statiustics needed) 

# In[8]:


# load data (load, allign coords, selects Tb and precip variable)
# tb = handle_OBS_data.load_clean_crop_tb(date,32) # tb and iwp need resampling to coarser grid=> they are loaded with a 2° buffer so resampling at the edges has enough data

# # load data
# precip = handle_OBS_data.load_clean_crop_imerg(date,30) # precip is ref grid => AOI is +-30° lat 


# # load data
# iwp = handle_OBS_data.load_clean_crop_ccic(date,32)


# combi function   
tb = handle_OBS_data.load_calc_clean_mean_tb(date, buffer = 32, min_images= 5)
precip = handle_OBS_data.load_calc_clean_mean_imerg(date, buffer = 30, min_images= 5)
iwp = handle_OBS_data.load_calc_clean_mean_ccic(date, buffer = 32, min_images= 5)

# resample (data, precip)
tb = handle_OBS_data.resample_grids(tb,precip)   # resampling to imerg ref grid => precip data is +- 30° => automatically cropped 
iwp = handle_OBS_data.resample_grids(iwp,precip)  

# tb = apply_regrid(tb, imerg)
# iwp = apply_regrid(iwp, imerg)


# # equivalent grid size in meters

# In[9]:


# # IMERG resolution

# dlon = 0.1   # degrees
# dlat = 0.1   # degrees

# lat0 = precip.latitude.mean().item()   

# R_earth = 6371e3

# dlambda = np.deg2rad(dlon)
# dphi     = np.deg2rad(dlat)
# phi0     = np.deg2rad(lat0)

# dA = R_earth**2 * np.cos(phi0) * dlambda * dphi
# dX = np.sqrt(dA)

# dX
#dX = 11119.492664455873


# # Prepare Data
# - convert the dataset into an Iris Cube (which is taken as tobac input)
# 

# In[10]:


# to iris cubes
tb_iris = tb.to_iris()
precip_iris = precip.to_iris()
iwp_iris = iwp.to_iris()


# expand time dim for tobac input (collapsed in the loading functions)
# import iris
tb_iris = iris.util.new_axis(tb_iris, scalar_coord='time')
precip_iris = iris.util.new_axis(precip_iris, scalar_coord='time')
iwp_iris = iris.util.new_axis(iwp_iris, scalar_coord='time')


# # add iwp layer

# In[11]:


# clean memory? 
# tb
# precip
# iwp
# tas
# dataset

# date - 1 
#date_previous ='2023-06-06-1500'

# Parse the string into a datetime object
from datetime import datetime, timedelta

dt = datetime.strptime(date, '%Y-%m-%d-%H%M')
dt_minus_3h = dt - timedelta(hours=3)
date_previous = dt_minus_3h.strftime('%Y-%m-%d-%H%M')

# load data
# data selection
vlist_tend= ["qsvi","clivi","qgvi","crs"]


# select timestamp and variables
iwp = handle_OBS_data.load_calc_clean_mean_ccic(date_previous, buffer = 32, min_images= 5)
iwp = handle_OBS_data.resample_grids(iwp,precip)  

# prepare data
# to iris cubes
iwp_iris_previous = iwp.to_iris()

# # expand time dim for tobac input (collapsed in the loading functions)
iwp_iris_previous = iris.util.new_axis(iwp_iris_previous, scalar_coord='time')



#####################
##### iwp tendency calc
# Remove time coord from both before arithmetic (or equalize them)
iwp_iris_previous_notime = iwp_iris_previous.copy()
iwp_iris_previous_notime.remove_coord('time')

iwp_iris_notime = iwp_iris.copy()
iwp_iris_notime.remove_coord('time')

# actual calc
dtiwp = (iwp_iris_notime - iwp_iris_previous_notime) / 3  # d iwp = kg/m2 pro 3h => durch 3 um stündliche Veränderung zu bekommen
# positive
dtiwp.data = np.where(dtiwp.data > 0, dtiwp.data, 0)

# Reattach the *current* timestamp's time coord to the result
# after subtraction, dtiwp already has the right shape (time_dim, lat, lon)
dtiwp.add_dim_coord(iwp_iris.coord('time'), 0)  # bind as DIM coord on dim 0, not a new axis


# rename so bulk stats putput is nice 
dtiwp.rename("dtiwp")          # sets long_name -> shows as "dtiwp" instead of "Unknown"
dtiwp.units = "kg m-2 h-1"     # correct units after the /3 (per-hour rate)
dtiwp.var_name = "dtiwp"

#dtiwp

# # as a side thing bc of added iwp values on cell mask
iwp_iris.rename("iwp")          # sets long_name -> shows as "dtiwp" instead of "Unknown"
iwp_iris.var_name = "iwp"

# dtiwp


# # 1. Anvil detection and segmentation
# ## 1.1. tobac detection on Tb image
# - use multiple threshold_anvil on BT data
# - from here on: same workflow for ICON and OBS

# ### Set detection parameter

# In[12]:


# set horizontal grid spacing [m] and temporal resolution [s]
#dxy =  dX # approx 11119# 10000 all data is in IMERG grid = approx. 10km # mcs detection use 1e5 * grid_spacing
# above 


# ### Perform feature detection

# In[13]:


# Perform feature detection:
print('starting anvil feature detection')
features = tobac.feature_detection.feature_detection_multithreshold(
    tb_iris, dxy, **feature_detection_params_anvil
)

print('anvil feature detection performed')


# ##  1.2. Segmentation of Anvils (on BT)
# - first filter!

# ### Filter results

# In[14]:


#filter for thres
filtered_features = features[features["threshold_value"] <= detection_threshold_anvil]


# In[15]:


print(features["hdim_2"].values.flags.writeable)
print(filtered_features["hdim_2"].values.flags.writeable)


# ### Set segmentation parameters

# In[16]:


segmentation_params_anvil = dict()
segmentation_params_anvil["method"] = "watershed"
segmentation_params_anvil["threshold"] = segmentation_threshold_anvil
segmentation_params_anvil["target"] = "minimum"
segmentation_params_anvil["PBC_flag"]='hdim_2'


# ### perform segmentation

# In[17]:


# import time
# t0 = time.time()
# # Perform segmentation:

print('Starting anvil segmentation.')
segmentation_mask_anvil, segmentation_features_anvil = tobac.segmentation.segmentation(
    filtered_features, tb_iris, dxy=dxy, **segmentation_params_anvil
)
print('segmentation anvil performed')

# t1 = time.time()
# print(f'segmentation anvil performed in {t1 - t0:.1f}s')


# ## 1.3. bulk statistics as post processing

# In[18]:


# calc bulk plus area
df_merged_anvil = use_tobac.add_bulk_stats_anvil(segmentation_features_anvil, segmentation_mask_anvil, tb_iris,precip_iris,iwp_iris)


df_merged_anvil["d_eq"] = use_tobac.add_D_equ(df_merged_anvil["area"])

df_merged_anvil = use_tobac.add_bulk_stats(df_merged_anvil, segmentation_mask_anvil, dtiwp, stats=["sum"])

print('Bulk stats anvils calculated')


# In[19]:


#df_merged_anvil


# ## 1.4.  Save mask and final features

# In[20]:


# save segmentation mask results
segmentation_mask_anvil_ds = xr.DataArray.from_iris(segmentation_mask_anvil)


# In[21]:


#########################
#####    ANVILS   #######
#########################

# # save mask
# segmentation_mask_anvil_ds.to_netcdf(
#     savedir / "anvil_mask" / f'mask_anvil_segmentation_{param_tag}_{date}.nc',
#     mode='w',
#     encoding={"segmentation_mask": {"zlib": True, "complevel": 4}}
# )

# save features
# if saveoutputs: 
#     df_merged_anvil.to_hdf(
#         savedir / "anvil_features" / f'features_anvil_segmentation_inkl_bulkstats_{param_tag}_{date}.h5',
#         key='table', mode='w'
#     )
    
#     print('anvil features with bulk statistics saved')


# # 2. Precip cell Detection and Segmentation on Precip image
# - started with nbook from fabian warmworld 03
# ## 2.1. tobac detection on precip image

# In[22]:


# set horizontal grid spacing [m] and temporal resolution [s]
# dxy is set above

# above


# In[23]:


# Perform feature detection:
print('starting cell feature detection')
features_cell = tobac.feature_detection_multithreshold(precip_iris, dxy, **feature_detection_params_cell)
print('cell feature detection performed')


# ## 2.2. Precip cell segmentation
# ### filter features

# In[24]:


#filter for thres
filtered_features_cell = features_cell[features_cell["threshold_value"] >= detection_threshold_cell]


# ### Set segmentation parameter

# In[25]:


# Dictionary containing keyword arguments for segmentation step:
segmentation_params_cell={}
segmentation_params_cell['method']='watershed'
segmentation_params_cell['threshold']=segmentation_threshold_cell 
segmentation_params_cell["target"] = "maximum" 
segmentation_params_cell["PBC_flag"]='hdim_2'


# ### perfrom segmentation

# In[26]:


# Perform segmentation:
print('Starting precip segmentation.')
segmentation_mask_cell, segmentation_features_cell =  tobac.segmentation.segmentation( #tobac.segmentation_2D(
    filtered_features_cell,precip_iris,dxy,**segmentation_params_cell)

print('segmentation precip performed')


# ## 2.3. Add bulk stats as post processing

# In[27]:


import use_tobac

# calc bulk plus area
df_merged_cell = use_tobac.add_bulk_stats_cell(segmentation_features_cell, segmentation_mask_cell, precip_iris)


df_merged_cell["d_eq"] = use_tobac.add_D_equ(df_merged_cell["area"])

df_merged_cell = use_tobac.add_bulk_stats(
	    df_merged_cell, segmentation_mask_cell, dtiwp, stats=["sum"])
	
df_merged_cell = use_tobac.add_bulk_stats(
	    df_merged_cell, segmentation_mask_cell, iwp_iris, stats=["sum", "mean"])

#print('Bulk stats precips calculated')


# In[28]:


#df_merged_cell


# ## 2.4. Save mask and final features

# In[29]:


# save segmentation mask results
segmentation_mask_cell_ds = xr.DataArray.from_iris(segmentation_mask_cell)

#########################
#####    Precip Cells   #######
#########################

# # save mask
# segmentation_mask_cell_ds.to_netcdf(
#     savedir / "cell_mask" / f'mask_cell_segmentation_{param_tag}_{date}.nc',
#     mode='w',
#     encoding={"segmentation_mask": {"zlib": True, "complevel": 4}}
# )

# # save features
# df_merged_cell.to_hdf(
#     savedir / "cell_features" / f'features_cell_segmentation_inkl_bulkstats_{param_tag}_{date}.h5',
#     key='table', mode='w'
# )

# print('cell features with bulk statistics saved')

# # 3. save detect and seg parameters

# In[30]:


if saveoutputs: 
    # save parameters as a small json next to it so you can always look up what was used
    import json
    
    params_path = savedir / f'params_anvil_{param_tag}.json'
    
    if not params_path.exists():
        params_to_save = {
            "detection_threshold_anvil": detection_threshold_anvil,
            "detection_threshold_cell": detection_threshold_cell,
            "feature_detection_params_anvil":   feature_detection_params_anvil,
            "segmentation_params_anvil":    segmentation_params_anvil,
            "feature_detection_params_cell":   feature_detection_params_cell,
            "segmentation_params_cell":    segmentation_params_cell,
        }
        with open(params_path, 'w') as f:
            json.dump(params_to_save, f, indent=4)
        print(f"params saved for tag: {param_tag}")
    else:
        print(f"params already exist for tag: {param_tag}, skipping")


# # 4. add Anvil charactistics to precip cell features
# Plan A: 
# 1. use precip cell centroids from cell features (latitude and longitude) to get in which anvils the cell lies => get feature anvil from mask anvil and add that to cell features
# 2. use feature anvil to join a selection of anvil features to cell features
# 
# Plan B: (USED)
# - use both segmentation masks
# - all precip cells that have a anvil above them anywhere, anvil id covering the most precip cell pixels is selected
# 

# In[31]:


## 4.1. A get anvil idx for each cell feature (precip cell centroid under anvil)
# # squeeze dims on length one (time) to be sure (does not really matter)
# segmentation_mask_anvil_ds_2d = segmentation_mask_anvil_ds.squeeze()

# df_merged_cell["lookup_anvil_feature"]= use_tobac.get_feature_of_segmask_for_feature_table(segmentation_mask_anvil_ds_2d,df_merged_cell)


# ## 4.1 B (precip cell mask under anvil) 
# 

# In[32]:


# create one dataset for masks 
combi_mask = segmentation_mask_anvil_ds.to_dataset(name="segmentation_mask_anvil")
combi_mask["segmentation_mask_cell"]=segmentation_mask_cell_ds
combi_mask = combi_mask.squeeze()
combi_mask

# get cell ids (could also come from feature table)
cell_ids = np.unique(combi_mask["segmentation_mask_cell"].values)
cell_ids = cell_ids[cell_ids!=0]


cell_to_anvil = {}
diagnostic_anvils_per_cell = {}
for cell_id in cell_ids:
    # get anvil values only where this cell is
    anvil_vals = combi_mask["segmentation_mask_anvil"].where(
        combi_mask["segmentation_mask_cell"] == cell_id).values.flatten()
    
    anvil_vals = anvil_vals[~np.isnan(anvil_vals) & (anvil_vals != 0)].astype(int)

    diagnostic_anvils_per_cell[int(cell_id)] = list(np.unique(anvil_vals).astype(int))
    
    if len(anvil_vals) > 0: # 1 to 1 match! 
        # pick anvil with most overlapping pixels
        unique, counts = np.unique(anvil_vals, return_counts=True)
        cell_to_anvil[int(cell_id)] = int(unique[np.argmax(counts)])

### add anvil look up table and update mask
# add anvil id look up in combined cell features
df_merged_cell["lookup_anvil_feature"] = df_merged_cell["feature"].map(cell_to_anvil).fillna(0).astype(int)


# update filtered masks to reflect 1 to 1 map
anvil_ids_final = set(cell_to_anvil.values())
cell_ids_final = set(cell_to_anvil.keys())

combi_mask["segmentation_mask_cell_filtered"] = combi_mask["segmentation_mask_cell"].where(
    combi_mask["segmentation_mask_cell"].isin(list(cell_ids_final)), other=0
)
combi_mask["segmentation_mask_anvil_filtered"] = combi_mask["segmentation_mask_anvil"].where(
    combi_mask["segmentation_mask_anvil"].isin(list(anvil_ids_final)), other=0
)


# ## 4.2. join selected anvil features by anvil_idx
# df_merged_anvil.columns
# 
#     Index(['frame', 'idx', 'hdim_1', 'hdim_2', 'num', 'threshold_value', 'feature', 'time', 'timestr', 'latitude', 'longitude', 'ncells', 'mean_iwp', 'total_iwp', 'max_iwp', 'mean_cell', 'total_cell', 'max_cell', 'min_tb', 'area', 'd_eq'], dtype='str')

# In[33]:


# select columns to join
anvil_columns_to_join = ['idx', 'hdim_1', 'hdim_2','num', 'threshold_value', 'feature','latitude', 'longitude','ncells', 'mean_iwp',
       'total_iwp', 'max_iwp','min_tb', 'area', 'd_eq','mean_precip', 'total_precip', 'max_precip',"total_dtiwp"]
df_merged_anvil_selection = df_merged_anvil[anvil_columns_to_join]

#df_merged_anvil_selection
df_merged_cell_combined = df_merged_cell.merge(df_merged_anvil_selection,
                                                   how = "inner" ,# left to keep all cell features # inner to only keep precip cells that have anvil
                                                   left_on = "lookup_anvil_feature",right_on = "feature",
                                                   suffixes=("_cell", "_anvil")) # change precip to cell => to distingish "variable precip" and precip CELL detection

# drop lookup_anvil_feature column bc its the same as feature_anvil
df_merged_cell_combined = df_merged_cell_combined.drop(columns=["lookup_anvil_feature"])


# # 4.4 save 

# In[34]:


# for var in combi_mask.data_vars:
#     print(var, combi_mask[var].attrs)
# print(combi_mask.attrs)


# In[35]:


if saveoutputs: 
    # save features
    df_merged_cell_combined.to_hdf(
        savedir / "cell_features_combined" / f'cell_features_combined_{param_tag}_{date}.h5',
        key='table', mode='w'
    )
    
    print('cell features combined with anvil properties saved')
    
    
    
    # # save mask
    # combi_mask.to_netcdf(
    #     savedir / "combi_mask" / f'mask_combi_{param_tag}_{date}.nc',
    #     mode='w',   engine="h5netcdf",
    #     encoding= {var: {"zlib": True, "complevel": 4} for var in combi_mask.data_vars}
    # )




# ## Diagnostics about join process

# In[36]:


# how many anvils per cell
anvils_per_cell = {cell_id: len(anvils) for cell_id, anvils in diagnostic_anvils_per_cell.items()}

print(f"total cells: {len(cell_to_anvil)}")
print(f"precentage of precip cells with >1 anvils: {100*(sum(v > 1 for v in anvils_per_cell.values()))/ (len(cell_to_anvil))} %")

print(f"cells with >1 anvil: {sum(v > 1 for v in anvils_per_cell.values())}")
print(f"max anvils per cell: {max(anvils_per_cell.values())}")


# In[37]:


# print some more information


# In[38]:


print(f"total anvil segmentated before intersection: { len(np.unique(combi_mask['segmentation_mask_anvil']))}")
#print(f"total anvils assigend to a cell before 1 to 1 filter: {len(anvil_ids_with_cells)}")
print(f"final anvils: {len(anvil_ids_final)}")


# how many cells per anvil 
anvil_to_cells = {}
for cell_id, anvil_id in cell_to_anvil.items():  # anvil_id is a single int, not a list
    anvil_to_cells.setdefault(anvil_id, []).append(cell_id)

cells_per_anvil = {anvil_id: len(cells) for anvil_id, cells in anvil_to_cells.items()}
print(f"\nanvils with >1 cell: {sum(v > 1 for v in cells_per_anvil.values())}")
print(f"max cells per anvil: {max(cells_per_anvil.values())}")



print(f"\ntotal cells segmentated (before intersection: { len(np.unique(combi_mask['segmentation_mask_cell']))}")
print(f"cells with anvil: {len(cell_ids_final)}")


# In[39]:


# some info on effect of filters to precip sum


# In[40]:


print(f"total filtered precipitation (mm/h): {np.sum(df_merged_cell.total_precip)}")
print(f"total filtered precipitation (mm/h): {np.sum(df_merged_cell_combined.total_precip_cell)}")

print(f"percentage of total precipitation cut bc cells do not have a matching anvil: {100-100*np.sum(df_merged_cell_combined.total_precip_cell)/np.sum(df_merged_cell.total_precip)} %")


total_precip_in_tropical_belt = precip.sum(dim = ["longitude","latitude"]).values


print(f"percentage of total rain in the tropical belt captured by the filtered cells: {np.sum(df_merged_cell_combined.total_precip_cell)/total_precip_in_tropical_belt} %")


# In[41]:


R = 6371
dlat = float(precip.latitude.diff("latitude").mean())
dlon = float(precip.longitude.diff("longitude").mean())
lat_rad = np.deg2rad(precip.latitude.values)

tropical_belt_area_km2 = ((R**2 * np.deg2rad(dlat) * np.deg2rad(dlon)) * np.cos(lat_rad)).sum() * 3600

print(f"area_covered_by_anvils before intersection: {np.sum(df_merged_anvil['area']) / 1e6 / tropical_belt_area_km2 * 100:.2f}%")
print(f"area_covered_by_anvils before after 1 to 1 join: {df_merged_cell_combined.drop_duplicates('feature_anvil')['area_anvil'].sum() / 1e6 / tropical_belt_area_km2 * 100:.2f}%")

