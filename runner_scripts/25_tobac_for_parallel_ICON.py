#!/usr/bin/env python
# coding: utf-8

# # tobac with detection on Tb - tryout for paralell
# - what this nbook does:
#     - Load ICON ngc4008, resampled to IMERG grid
# 
#     - tobac application:
#         - anvils 
#             - detect on Tb 
#             - segmentate on Tb 
#             - bulk stats of IWP 
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


import handle_ICON_data as ic

from defs_application import georegions 
import use_tobac
import plots_mapping


# # arguments

# In[3]:


# set date
#date = "2023-06-06-2100"
# date = sys.argv[1]

# threshold_anvils
detection_threshold_anvil = 225 # K, needs to be part of multi_detection_thresholds_anvil
multi_detection_thresholds_anvil =  [225]  # [210,215,225,230, 235,241] ## K # = detection_threshold_anvil
segmentation_threshold_anvil = 241 # K 235 # bolot 235, feng MCSIMP =< 240, Senf 230

# threhold precip
detection_threshold_cell = 10
multi_detection_thresholds_cell = [10] #[1,2,3,5,10] # mm/h # brueck 2020 => string convective features => detection high, to segmentate cell => lower threshold
segmentation_threshold_cell = 10 # 0.1 brueck 2020. 10 senf

# build a descriptive tag from your parameters
param_tag = f"anvil_detectthres{detection_threshold_anvil}_seg{segmentation_threshold_anvil}_cell_detectthres{detection_threshold_cell}_seg{segmentation_threshold_cell}"
#param_tag


###########
compute_hist_diagnostic = True



if "launcher" in sys.argv[0]: 
    date = "2023-06-06-1800"
    interactive =True
    saveoutputs = True
    savedir = Path("../output/apply/apply_ICON_with_mask_from_nbook") / date # second_tune_OBS tobactryoutsdata_OBS

else: 
    date = sys.argv[1]
    interactive = False
    saveoutputs = True
    savedir = Path("../output/second_tune_ICON") / param_tag  #apply/apply_ICON_with_mask"
    
print(date)


# In[4]:


############# ANVILS ############
# detection para (Tb)
feature_detection_params_anvil = dict()
feature_detection_params_anvil["threshold"] = multi_detection_thresholds_anvil
feature_detection_params_anvil["target"] = "minimum"
feature_detection_params_anvil["position_threshold"] = "weighted_diff"
feature_detection_params_anvil["PBC_flag"]='hdim_2'


# Gaussian smoothing before detection
feature_detection_params_anvil["sigma_threshold"] = 0.5# 0.05 # 0.05  

# from below 
dX = 11119.492664455873
dxy =  dX 

# minimum number of pixels below threshold_anvil
#feature_detection_params_anvil["n_min_threshold"] = 3 # one pixel approx 10km * 10km = 100km2

# minimum pixel distance to next feature
feature_detection_params_anvil["min_distance"]= dxy*20  # mcs ICON trakcing example *4 => aber wir haben geresamplet zu 11 x 11km 


# In[5]:


############# CELLS ############
# detection para (Tb)
feature_detection_params_cell = dict()
feature_detection_params_cell["threshold"] = multi_detection_thresholds_cell
feature_detection_params_cell["target"] = "maximum"
feature_detection_params_cell["position_threshold"] = "weighted_diff"
feature_detection_params_cell["PBC_flag"]='hdim_2'


# Gaussian smoothing before detection
feature_detection_params_cell["sigma_threshold"] = 0.05
feature_detection_params_cell["n_min_threshold"] = 3 # brueck


# In[6]:


# create main directory
savedir.mkdir(parents=True, exist_ok=True)

# define subdirectories
subdirs = [
    #"cell_features",
    "anvil_features",
    "cell_features_combined",
    "combi_mask",
    "plots"
]

# create all subdirectories
for sub in subdirs:
    (savedir / sub).mkdir(parents=True, exist_ok=True)

# plots dir
plots_dir = savedir / "plots"


# # load data

# In[7]:


# data selection
zoom = 9 # approx. 14km, => IMERG is 11km
vlist = ["pr", "rlut", "tas", "qsvi","clivi","qgvi","crs"]

# load data
dataset = ic.open_ngc4008(zoom = zoom) 

# select timestamp and variables
dataset = ic.select_time(dataset, date)
dataset = ic.select_vars(dataset, vlist)

# calculate input variables 
dataset = ic.add_input_vars(dataset)
dataset


# resample to Imerg grid
tas= ic.resample_to_lon_lat(dataset, "tas", zoom= zoom,to_imerg = True)
tb = ic.resample_to_lon_lat(dataset, "tb_11", zoom= zoom, to_imerg = True)
precip= ic.resample_to_lon_lat(dataset, "rain_tot_rate", zoom= zoom, to_imerg = True)
iwp = ic.resample_to_lon_lat(dataset, "iwp",zoom= zoom, to_imerg = True)


# # equivalent grid size in meters

# In[8]:


# IMERG resolution

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

# dX = 11119.492664455873
# dxy =  dX 


# # Prepare Data
# In the next steps, we
# - (regular grid)
# - resmaple to imerg data so everything has same resolution (for bulk statiustics needed) 
# - convert the dataset into an Iris Cube (which is taken as tobac input)
# 

# In[9]:


# to iris cubes
tb_iris =tb.to_iris()
precip_iris = precip.to_iris()
iwp_iris = iwp.to_iris()

tas_iris = tas.to_iris()

# # expand time dim for tobac input (collapsed in the loading functions)
# import iris
tb_iris = iris.util.new_axis(tb_iris, scalar_coord='time')
precip_iris = iris.util.new_axis(precip_iris, scalar_coord='time')
iwp_iris = iris.util.new_axis(iwp_iris, scalar_coord='time')

tas_iris =  iris.util.new_axis(tas_iris, scalar_coord='time')


# # Anvil detection and segmentation
# ## 1.1 tobac detection on Tb image
# - use multiple threshold on BT data
# - from here on: same workflow for ICON and OBS

# ### Set detection parameter

# In[10]:


# set horizontal grid spacing [m] and temporal resolution [s]
# approx 11119# 10000 all data is in IMERG grid = approx. 10km # mcs detection use 1e5 * grid_spacing


# ### Perform feature detection

# In[11]:


# Perform feature detection:
print('starting anvil feature detection')
features = tobac.feature_detection.feature_detection_multithreshold(
    tb_iris, dxy, **feature_detection_params_anvil
)

print('anvil feature detection performed')


# ## 1.2. Segmentation of Anvils (on BT)
# - first filter!

# ### Filter results
# old

# In[12]:


# filter for thres
filtered_features = features[features["threshold_value"] <= detection_threshold_anvil]


print(features["hdim_2"].values.flags.writeable)
print(filtered_features["hdim_2"].values.flags.writeable)


# ### Set segmentation parameters

# In[13]:


segmentation_params_anvil = dict()
segmentation_params_anvil["method"] = "watershed"
segmentation_params_anvil["threshold"] = segmentation_threshold_anvil
segmentation_params_anvil["target"] = "minimum"
segmentation_params_anvil["PBC_flag"]='hdim_2'


# ### perform segmentation

# In[14]:


# Perform segmentation:
print('Starting anvil segmentation.')
segmentation_mask_anvil, segmentation_features_anvil = tobac.segmentation.segmentation(
    filtered_features, tb_iris, dxy=dxy, **segmentation_params_anvil
)
print('segmentation anvil performed')


# # 1.3. bulk statistics as post processing

# In[15]:


#help(tobac.calculate_area)


# In[16]:


# calc bulk plus area
df_merged_anvil = use_tobac.add_bulk_stats_anvil(segmentation_features_anvil, segmentation_mask_anvil, tb_iris,precip_iris,iwp_iris)



# d eq
df_merged_anvil["d_eq"] = use_tobac.add_D_equ(df_merged_anvil["area"])

# add tas
df_merged_anvil = use_tobac.add_bulk_stats(
    df_merged_anvil, segmentation_mask_anvil, tas_iris, stats=["mean"]
)


print('Bulk stats anvils calculated')


# ## 1.4.  Save mask and final features

# In[17]:


# save segmentation mask results
segmentation_mask_anvil_ds = xr.DataArray.from_iris(segmentation_mask_anvil)


# In[18]:


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
if saveoutputs: 
    df_merged_anvil.to_hdf(
        savedir / "anvil_features" / f'features_anvil_segmentation_inkl_bulkstats_{param_tag}_{date}.h5',
        key='table', mode='w'
    )
    
    print('anvil features with bulk statistics saved')


# # 2. Precip cell Detection and Segmentation on Precip image
# - started with nbook from fabian warmworld 03
# ## 2.1. tobac detection on precip image

# In[19]:


# set horizontal grid spacing [m] and temporal resolution [s]
# dxy is set above

# above


# In[20]:


# Perform feature detection:
print('starting cell feature detection')
features_cell = tobac.feature_detection_multithreshold(precip_iris, dxy, **feature_detection_params_cell)
print('cell feature detection performed')


# ## 2.2. Precip cell segmentation
# ### filter features

# In[21]:


#filter for thres
filtered_features_cell = features_cell[features_cell["threshold_value"] >= detection_threshold_cell]


# ### set segmentation üarameter

# In[22]:


# Dictionary containing keyword arguments for segmentation step:
segmentation_params_cell={}
segmentation_params_cell['method']='watershed'
segmentation_params_cell['threshold']=segmentation_threshold_cell 
segmentation_params_cell["target"] = "maximum"
segmentation_params_cell["PBC_flag"]='hdim_2'


# ### perfrom segmentation

# In[23]:


# Perform segmentation:
print('Starting precip segmentation.')
segmentation_mask_cell, segmentation_features_cell =  tobac.segmentation.segmentation( #tobac.segmentation_2D(
    filtered_features_cell,precip_iris,dxy,**segmentation_params_cell)

print('segmentation precip performed')


# ## 2.3. Add bulk stats as post processing

# In[24]:


import use_tobac

# calc bulk plus area
df_merged_cell = use_tobac.add_bulk_stats_cell(segmentation_features_cell, segmentation_mask_cell, precip_iris)


df_merged_cell["d_eq"] = use_tobac.add_D_equ(df_merged_cell["area"])

# add tas
df_merged_cell = use_tobac.add_bulk_stats(
    df_merged_cell, segmentation_mask_cell, tas_iris, stats=["mean"]
)


#print('Bulk stats precips calculated')


# In[25]:


#df_merged_cell


# ## 2.4. Save mask and final features

# In[26]:


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

# In[27]:


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

# In[28]:


## 4.1. A get anvil idx for each cell feature (precip cell centroid under anvil)
# # squeeze dims on length one (time) to be sure (does not really matter)
# segmentation_mask_anvil_ds_2d = segmentation_mask_anvil_ds.squeeze()

# df_merged_cell["lookup_anvil_feature"]= use_tobac.get_feature_of_segmask_for_feature_table(segmentation_mask_anvil_ds_2d,df_merged_cell)


# ## 4.1 B (precip cell mask under anvil) 
# 

# In[29]:


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

# In[30]:


# select columns to join
anvil_columns_to_join = ['idx', 'hdim_1', 'hdim_2','num', 'threshold_value', 'feature','latitude', 'longitude','ncells', 'mean_iwp',
       'total_iwp', 'max_iwp','min_tb', 'area', 'd_eq','mean_precip', 'total_precip', 'max_precip']
df_merged_anvil_selection = df_merged_anvil[anvil_columns_to_join]

#df_merged_anvil_selection
df_merged_cell_combined = df_merged_cell.merge(df_merged_anvil_selection,
                                                   how = "inner" ,# left to keep all cell features # inner to only keep precip cells that have anvil
                                                   left_on = "lookup_anvil_feature",right_on = "feature",
                                                   suffixes=("_cell", "_anvil")) # change precip to cell => to distingish "variable precip" and precip CELL detection

# drop lookup_anvil_feature column bc its the same as feature_anvil
df_merged_cell_combined = df_merged_cell_combined.drop(columns=["lookup_anvil_feature"])


# # 4.4 save 

# In[31]:


if saveoutputs:   
    # save features
    df_merged_cell_combined.to_hdf(
        savedir / "cell_features_combined" / f'cell_features_combined_{param_tag}_{date}.h5',
        key='table', mode='w'
    )
    
    print('cell features combined with anvil properties saved')
    
    
    
    # save mask
    combi_mask.to_netcdf(
        savedir / "combi_mask" / f'mask_combi_{param_tag}_{date}.nc',
        mode='w',
        encoding= {var: {"zlib": True, "complevel": 4} for var in combi_mask.data_vars}
    
    )


# ## Diagnostics about join process

# In[32]:


# how many anvils per cell
anvils_per_cell = {cell_id: len(anvils) for cell_id, anvils in diagnostic_anvils_per_cell.items()}

print(f"total cells: {len(cell_to_anvil)}")
print(f"precentage of precip cells with >1 anvils: {100*(sum(v > 1 for v in anvils_per_cell.values()))/ (len(cell_to_anvil))} %")

print(f"cells with >1 anvil: {sum(v > 1 for v in anvils_per_cell.values())}")
print(f"max anvils per cell: {max(anvils_per_cell.values())}")


# In[33]:


# print some more information


# In[34]:


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


# In[35]:


df_merged_cell_combined.columns


# In[36]:


# some info on effect of filters to precip sum


# In[37]:


print(f"total filtered precipitation (mm/h): {np.sum(df_merged_cell.total_precip)}")
print(f"total filtered precipitation (mm/h): {np.sum(df_merged_cell_combined.total_precip_cell)}")

print(f"percentage of total precipitation cut bc cells do not have a matching anvil: {100-100*np.sum(df_merged_cell_combined.total_precip_cell)/np.sum(df_merged_cell.total_precip)} %")


total_precip_in_tropical_belt = precip.sum(dim = ["longitude","latitude"]).values


print(f"percentage of total rain in the tropical belt captured by the filtered cells: {np.sum(df_merged_cell_combined.total_precip_cell)/total_precip_in_tropical_belt} %")


# In[38]:


R = 6371
dlat = float(precip.latitude.diff("latitude").mean())
dlon = float(precip.longitude.diff("longitude").mean())
lat_rad = np.deg2rad(precip.latitude.values)

tropical_belt_area_km2 = ((R**2 * np.deg2rad(dlat) * np.deg2rad(dlon)) * np.cos(lat_rad)).sum() * 3600

print(f"area_covered_by_anvils before intersection: {np.sum(df_merged_anvil['area']) / 1e6 / tropical_belt_area_km2 * 100:.2f}%")
print(f"area_covered_by_anvils before after 1 to 1 join: {df_merged_cell_combined.drop_duplicates('feature_anvil')['area_anvil'].sum() / 1e6 / tropical_belt_area_km2 * 100:.2f}%")


# # Some diagnostics about the cell sthat get deleted

# In[39]:


if compute_hist_diagnostic:
    ## add BT min to cell featurs 
    # add BT min
    tb_iris.rename("tb")
    df_merged_cell_new = use_tobac.add_bulk_stats(
        df_merged_cell, segmentation_mask_cell, tb_iris, stats=["min"]
    )
    
    
    # select columns to join
    anvil_columns_to_join = ['idx', 'hdim_1', 'hdim_2','num', 'threshold_value', 'feature','latitude', 'longitude','ncells', 'mean_iwp',
           'total_iwp', 'max_iwp','min_tb', 'area', 'd_eq','mean_precip', 'total_precip', 'max_precip']
    df_merged_anvil_selection = df_merged_anvil[anvil_columns_to_join]
    
    # LEFT merge to keep ALL precip cell features
    df_merged_cell_combined_all = df_merged_cell_new.merge(
        df_merged_anvil_selection,
        how="left",
        left_on="lookup_anvil_feature",
        right_on="feature",
        suffixes=("_cell", "_anvil")
    ).drop(columns=["lookup_anvil_feature"])
    
    
    # Split: precip features WITH a matched anvil
    df_merged_cell_combined_test = df_merged_cell_combined_all[
        df_merged_cell_combined_all["feature_anvil"].notna()
    ].copy()
    
    # Split: precip features WITHOUT a matched anvil
    df_precip_no_anvil = df_merged_cell_combined_all[
        df_merged_cell_combined_all["feature_anvil"].isna()
    ].copy()



# In[40]:


if compute_hist_diagnostic:
    import pandas as pd
    
    toplot = ["min_tb_cell"]
    label = "Min. BT of cell"
    nbins = 40
    
    color2= "sandybrown"
    color1= "darkslateblue"
    
    sns.set_context("talk")
    fig, ax = plt.subplots(1, figsize=(7, 4.5))
    
    col = toplot[0]  # extract string from list
    
    combined = pd.concat([df_merged_cell_combined_test[col], df_precip_no_anvil[col]]).dropna()
    bins = np.linspace(combined.min(), combined.max(), nbins + 1)
    
    ax.hist(df_merged_cell_combined_test[col].dropna(), bins=bins, alpha=0.7, label="with anvil", color= color1 )
    ax.hist(df_precip_no_anvil[col].dropna(), bins=bins, alpha=0.7, label="no anvil", color= color2)
    ax.set_title(label, fontweight = "bold")
    ax.set_ylabel("Cell Counts (#)")
    ax.set_xlabel("BT (K)")
    
    median1 = df_merged_cell_combined_test[col].median()
    median2 = df_precip_no_anvil[col].median()
    ax.axvline(median1, color=color1, linestyle="--", linewidth=2, label=f"median = {median1:.1f} K")
    ax.axvline(median2, color=color2, linestyle="--", linewidth=2, label=f"median = {median2:.1f} K")
    
    
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels,
               loc="lower center",
               bbox_to_anchor=(0.5, -0.15),
               ncol=len(labels)//2,
               frameon=False)
    
    sns.despine()
    plt.tight_layout()
    if saveoutputs: 
        fig.savefig(os.path.join(plots_dir,f"histogram_BT_deleted_selected_cells_{date}.pdf"),dpi=150, bbox_inches='tight')
    plt.show()


# In[54]:


if compute_hist_diagnostic:
    import pandas as pd
    toplot = ["min_tb_cell","total_precip_cell","area_cell"]
    labelssub = ["a) min. BT","b) total precip.", "c) area"]
    xlabels = ["(K)", "(mm hr$^{-1}$)", "(m$^2$)"]
    
    # df_merged_cell_combined_test
    # df_precip_no_anvil
    nbins = 40 
    sns.set_context("talk")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    
    
    for ax, col, label,xlabel in zip(axes, toplot,labelssub,xlabels):
        combined = pd.concat([df_merged_cell_combined_test[col], df_precip_no_anvil[col]]).dropna()
        bins = np.linspace(combined.min(), combined.max(), nbins+1)  # 40 bins
        ax.hist(df_merged_cell_combined_test[col].dropna(), bins=bins
                , alpha=0.6, label="cells with anvil", color= color1)
        ax.hist(df_precip_no_anvil[col].dropna(), bins=bins, alpha=0.6, label="cells with no anvil",color= color2)
        ax.set_ylabel("Counts(#)")
        ax.set_xlabel(xlabel)
        ax.set_title(label, fontweight = "bold")
    
    
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
               loc="lower center",
               bbox_to_anchor=(0.5, -0.05),  # slightly below the plots
               ncol=len(labels),
               frameon=False)
    sns.despine()
    plt.tight_layout()
    plt.show()


# In[42]:


if compute_hist_diagnostic:
    import math
    import pandas as pd 
    
    toplot = ['mean_precip_cell',
           'total_precip_cell', 'max_precip_cell', 'area_cell', 'min_tb_cell']
    
    # df_merged_cell_combined_test
    # df_precip_no_anvil
    ncols = 3
    n = len(toplot)
    
    nrows = math.ceil(n / ncols)
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))
    axes = axes.flatten()
    
    
    for ax, col in zip(axes, toplot):
        combined = pd.concat([df_merged_cell_combined_test[col], df_precip_no_anvil[col]]).dropna()
        bins = np.linspace(combined.min(), combined.max(), 41)  # 40 bins
    
        ax.hist(df_merged_cell_combined_test[col].dropna(), bins=40, alpha=0.6, label="with anvil", density = False,color= color1)
        ax.hist(df_precip_no_anvil[col].dropna(), bins=40, alpha=0.6, label="no anvil", density = False,color= color2)
        ax.set_title(col, fontweight= "bold")
        ax.set_ylabel("Counts(#)")
    
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
               loc="lower center",
               bbox_to_anchor=(0.5, -0.05),  # slightly below the plots
               ncol=len(labels),
               frameon=False)
    
    for ax in axes[n:]:
        ax.set_visible(False)
    sns.despine()
    plt.tight_layout()
    plt.show()


# # 5. plots for quick eval
# 
# ## Quick plot Anvils

# In[43]:


seg2d_anvil = combi_mask["segmentation_mask_anvil"].squeeze()
seg2d_anvil_filtered = combi_mask["segmentation_mask_anvil_filtered"].squeeze()
seg2d_cell = combi_mask["segmentation_mask_cell"].squeeze()
seg2d_cell_filtered = combi_mask["segmentation_mask_cell_filtered"].squeeze()

# bg layer where all pixels that represent a deselected cell are assigned same value=> so they appear the same grey
seg2d_anvil_bg = seg2d_anvil.where(seg2d_anvil == 0, other=1)
seg2d_cell_bg = seg2d_cell.where(seg2d_cell== 0, other=1)
#seg2d_cell_bg

# cretae colormaps ONCE
cmap_anvil, norm_anvil = plots_mapping.build_id_cmap([seg2d_anvil, seg2d_anvil_filtered], seed=0)
cmap_cell,  norm_cell  = plots_mapping.build_id_cmap([seg2d_cell,  seg2d_cell_filtered],  seed=1)

date_title = plots_mapping.title_time_format(segmentation_mask_anvil_ds)

threshold_anvil = int(seg2d_anvil.attrs["threshold"])
unit_threshold_anvil = "K"


threshold_cell = float(seg2d_cell.attrs["threshold"])
unit_threshold_cell = "mm/h"



# In[44]:


# #plt.style.use("tex")
# sns.set_context("talk")

# # def georegion 
# georegion = "africa_0"

# # plot

# fig,ax,_ = plots_mapping.domain_plot_seg_mask(seg2d_anvil,
#                                               #background= tb,cmap_background = plots_mapping.tb_colormap(),
#                                               domain=  georegions[georegion],cmap=cmap_anvil,norm = norm_anvil, figsize=(10,8),
#                                           title = f'Anvil Segmentation (Segmentation threshold = {threshold_anvil} {unit_threshold_anvil}) {date_title}')
# # box in the lower right (is shown in the saved picture)
# plots_mapping.add_para_selection_info(fig, 
#                                       detection_threshold_anvil = detection_threshold_anvil,
#                                       feature_detection_params_anvil = feature_detection_params_anvil,
#                                       segmentation_params_anvil= segmentation_params_anvil)

#fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_anvils_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')
# ## Quick plot precip 

# In[45]:


# sns.set_context("talk")
# #plt.style.use('tex')

# # def georegion 
# georegion = "africa_0"

# # plot

# #cmap_cell,_,_ = plots_mapping.cell_colormap()

# fig,ax,_ = plots_mapping.domain_plot_seg_mask(seg2d_cell,#background = precip, cmap_background = cmap_cell, 
#                                               domain=  georegions[georegion],cmap=cmap_cell,norm = norm_cell,figsize=(10,8),
#                                           title = f'Precip Cells (Segmentation threshold = {threshold_cell} {unit_threshold_cell}) {date_title}')
# # box in the lower right (is shown in the saved picture)
# plots_mapping.add_para_selection_info(fig,
#                                       feature_detection_params_cell=  feature_detection_params_cell,
#                                       segmentation_params_cell= segmentation_params_cell)


#fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_precip_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')
# # combined plot

# In[46]:


# sns.set_context("talk")
# #plt.style.use('tex')

# # def georegion 
# #georegion = "africa_0"

# for georegion in georegions.keys():
#     if georegion == "global":
#         continue
   
#     lon_min, lon_max, lat_min, lat_max = georegions[georegion]
#     lon_extent = lon_max - lon_min
#     lat_extent = lat_max - lat_min

#     fig_width = 15
#     fig_height = fig_width * (lat_extent / lon_extent) * (2 / 2)
#     fig_height = max(5, min(fig_height, 20))  # clamp

#     # plot
#     fig, axes = plt.subplots(
#         2, 2,
#         figsize=(fig_width, fig_height),
#         subplot_kw={"projection": ccrs.PlateCarree()},
#         constrained_layout = True
#     )
    
#     # tb image
#     fig, axes[0, 0], _ = plots_mapping.domain_plot_tb(tb, domain=georegions[georegion], title="a) Brightness Temperature", fig=fig, ax=axes[0, 0])
#     # anvil seg
#     fig, axes[0, 1], _ = plots_mapping.domain_plot_seg_mask(seg2d_anvil, cmap=cmap_anvil,norm = norm_anvil,left_grid_label=False,domain=georegions[georegion], title="b) Anvil Segmentation", fig=fig, ax=axes[0, 1])
#     # precip image
#     fig, axes[1, 0], _ = plots_mapping.domain_plot_precip(precip,vmin = 0, vmax = 10, domain=georegions[georegion], title="c) Precipitation", fig=fig, ax=axes[1, 0])
#     # precip seg
#     fig, axes[1, 1], _ = plots_mapping.domain_plot_seg_mask(seg2d_cell, domain=georegions[georegion],left_grid_label=False,cmap=cmap_cell,norm = norm_cell, title="d) Precipitation Cell Segmentation", fig=fig, ax=axes[1, 1])
    
#     fig.suptitle(f"{date_title}", fontweight="bold")
    
#     # solve unequal subplot soizes due to colorbar
#     # reserve colorbar space for segmentation plot
#     dummy = plt.cm.ScalarMappable(cmap="Greys")
#     cbar = fig.colorbar(dummy, ax=axes[0, 1], fraction=0.046, pad=0.04)
#     cbar.ax.set_visible(False)
#     cbar = fig.colorbar(dummy, ax=axes[1, 1], fraction=0.046, pad=0.04)
#     cbar.ax.set_visible(False)
    
#     #plt.tight_layout()
    
#     #fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_combined_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')
    
#     plt.show()
    


# # one global plot

# In[47]:


georegion = "global"
#plt.style.use('tex')
sns.set_context("talk")

fig, axes = plt.subplots(
    2, 1,
    figsize=(15, 6),
    subplot_kw={"projection": ccrs.PlateCarree()}
)

fig,axes[0], _ = plots_mapping.domain_plot_seg_mask(seg2d_anvil,cmap=cmap_anvil,norm = norm_anvil,
                                                    domain=  georegions[georegion],
                                                    title = f'Anvils', fig = fig, ax = axes[0])
fig,axes[1], _= plots_mapping.domain_plot_seg_mask(seg2d_cell,cmap=cmap_cell,norm = norm_cell,
                                                   domain=  georegions[georegion],
                                                   title = f'Precipitation Cells', fig = fig, ax = axes[1])

fig.suptitle(f"{date_title}", fontweight="bold")

plt.tight_layout()
plt.show()


# In[48]:


if saveoutputs: 
    fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_combi_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')


# # combi plot iwthfiltered anvils

# In[49]:


from matplotlib.colors import ListedColormap

bg_cmap = ListedColormap([
    (1, 1, 1, 0.0),   # 0 → fully transparent
    (0.75, 0.75, 0.75, 1.0)  # 1 → light grey (darker than before)
])

sns.set_context("talk")
#plt.style.use('tex')

# def georegion 
georegion = ["africa_0"]

#for georegion in  georegions.keys(): #georegion:
for georegion in  georegion:
    if georegion == "global":
        continue

    lon_min, lon_max, lat_min, lat_max = georegions[georegion]
    lon_extent = lon_max - lon_min
    lat_extent = lat_max - lat_min

    fig_width = 15
    # account for ~10% width lost to colorbars on col 0
    effective_lon = lon_extent * 0.90
    fig_height = fig_width * (lat_extent / effective_lon) * (2 / 3)
    fig_height = max(5, min(fig_height, 20))

    # plot
    fig, axes = plt.subplots(
        2, 3,
        figsize=(fig_width, fig_height),
        subplot_kw={"projection": ccrs.PlateCarree()},
        constrained_layout = True
    )
    
    # tb image
    _, axes[0, 0], _ = plots_mapping.domain_plot_tb(tb, domain=georegions[georegion],left_grid_label=True,bottom_grid_label = True, title="a) Brightness Temperature", fig=fig, ax=axes[0, 0])
    # anvil seg
    _, axes[0, 1], _ = plots_mapping.domain_plot_seg_mask(seg2d_anvil, cmap=cmap_anvil,norm = norm_anvil,domain=georegions[georegion],left_grid_label=False,bottom_grid_label = True, title="b) Anvils", fig=fig, ax=axes[0, 1])
    # anvil seg
    _, axes[0, 2], _ = plots_mapping.domain_plot_seg_mask(seg2d_anvil_filtered,cmap=cmap_anvil,norm = norm_anvil, domain=georegions[georegion], left_grid_label=False,bottom_grid_label = True,
                                                            background=seg2d_anvil_bg,cmap_background=bg_cmap,#"Greys",
                                                            title="c) Selected Anvils ", fig=fig, ax=axes[0, 2])
    
    # precip image
    _, axes[1, 0], _ = plots_mapping.domain_plot_precip(precip,vmin = 0, vmax = 10, domain=georegions[georegion], left_grid_label=True,bottom_grid_label = True,title="d) Precipitation", fig=fig, ax=axes[1, 0])
    # precip seg
    _, axes[1, 1], _ = plots_mapping.domain_plot_seg_mask(seg2d_cell,cmap=cmap_cell,norm = norm_cell, domain=georegions[georegion],left_grid_label=False,bottom_grid_label = True, title="e) Precipitation Cells", fig=fig, ax=axes[1, 1])
    # precip seg
    _, axes[1, 2], _ = plots_mapping.domain_plot_seg_mask(seg2d_cell_filtered, cmap=cmap_cell,norm = norm_cell,domain=georegions[georegion], left_grid_label=False,bottom_grid_label = True,
                                                            background=seg2d_cell_bg,cmap_background=bg_cmap,#"Greys",
                                                            title="f) Selected Precipitation Cells", fig=fig, ax=axes[1, 2])
    
    fig.suptitle(f"{date_title}", fontweight="bold")
    
    # solve unequal subplot soizes due to colorbar
    dummy = plt.cm.ScalarMappable(cmap="Greys")
    cbar = fig.colorbar(dummy, ax=axes[0, 1], fraction=0.046, pad=0.04)
    cbar.ax.set_visible(False)
    cbar = fig.colorbar(dummy, ax=axes[1, 1], fraction=0.046, pad=0.04)
    cbar.ax.set_visible(False)
    cbar = fig.colorbar(dummy, ax=axes[0, 2], fraction=0.046, pad=0.04)
    cbar.ax.set_visible(False)
    cbar = fig.colorbar(dummy, ax=axes[1, 2], fraction=0.046, pad=0.04)
    cbar.ax.set_visible(False)

    #plt.tight_layout()
    
    if saveoutputs: 
        fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_combined_filtered_cells_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')
   
    fig.canvas.draw()

    plt.show()
    plt.close(fig)
   


# In[50]:


georegion = "global"
#plt.style.use('tex')
sns.set_context("talk")

fig, axes = plt.subplots(
    2, 1,
    figsize=(15, 6),
    subplot_kw={"projection": ccrs.PlateCarree()}
)

fig,axes[0], _ = plots_mapping.domain_plot_seg_mask(seg2d_anvil,cmap=cmap_anvil,norm = norm_anvil,
                                                    domain=  georegions[georegion],
                                                    title = f'Anvils', fig = fig, ax = axes[0])
fig,axes[1], _= plots_mapping.domain_plot_seg_mask(seg2d_anvil_filtered,cmap=cmap_anvil,norm = norm_anvil,
                                                   domain=  georegions[georegion],
                                                   title = f'Filtered Anvils', fig = fig, ax = axes[1])

fig.suptitle(f"{date_title}", fontweight="bold")

plt.tight_layout()
plt.show()


# In[51]:


if saveoutputs: 
    fig.savefig(os.path.join(plots_dir,f"quickplot_segmentation_OBS_anvil_beforeandafter_{georegion}_{param_tag}_{date}.pdf"),dpi=150, bbox_inches='tight')

