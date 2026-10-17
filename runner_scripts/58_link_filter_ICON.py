#!/usr/bin/env python
# coding: utf-8

# # link features in 30 yrs simulation
# - 51 and 53 in one for the 30 yrs ICON dataset
# 
# - link 

# In[ ]:


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


import numpy as np
import xarray as xr
import os
import pandas as pd

from pathlib import Path

# Import tobac itself:
import tobac
import tobac.utils

print("using tobac version", str(tobac.__version__))

import iris

# some eval plotting
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import seaborn as sns

import h5py
import sys

import glob

# import use_tobac

sys.path.append("../tools")
from defs_application import bad_timesteps
import plots_mapping as pm


# In[ ]:


model = "ICON"
timeperiod = "FULL"
year =  sys.argv[1] # "2026-01" # some pattern for which searched

inputdir = Path(f"../output/apply_seg/apply_{model}/{timeperiod}/cell_features_combined_envfeatures")
#saveoutputs = True

savedir_filtered = Path(f"../output/linking/filtered")
# create main directory
savedir_filtered.mkdir(parents=True, exist_ok=True)



# # import feature tables

# In[3]:


files = sorted(glob.glob(f'{inputdir}/*{year}*.h5'))
df = []
for file in files:
    data = pd.read_hdf(file, key='table')  
    #print(file)
    data = data.reset_index(drop=True)
    df.append(data)

features = pd.concat(df, ignore_index=True) 

# fix corrupted time column from HDF5 precision issue, use timestr as ground truth
features['time'] = pd.to_datetime(features['timestr'])
features['time'] = features['time'].astype('datetime64[ns]')
# reset index
features = features.sort_values('time').reset_index(drop=True)  # sort here


# filter 5 bad days
features = features[~features['time'].isin(bad_timesteps)].reset_index(drop=True)


# rename columns so tobac can identify them
features = features.rename(columns={"hdim_1_cell": "hdim_1", "hdim_2_cell": "hdim_2"})
features = features.rename(columns={"longitude_cell": "longitude", "latitude_cell": "latitude"})
features = features.rename(columns={"feature_cell": "feature"})

# frame number was deleted by individual detection
full_time_grid = pd.date_range(start=features['time'].min(),end=features['time'].max(),freq='3h').astype('datetime64[ns]')
time_to_frame = {t: i for i, t in enumerate(full_time_grid)}
features['frame'] = features['time'].map(time_to_frame)



# # Linking

# In[4]:


dxy = 11119.492664455873
dt = 10800 #s = 3h*3600
vmax = 20
stubs =1


# In[5]:


Tracks = tobac.linking_trackpy(
    features, # detected features
    None, # needs to be none (input field, not used in tobac version)
    dt=dt, dxy=dxy, 
    v_max=vmax,
    method_linking="predict", 
    stubs=stubs,   
    adaptive_stop = 0.2,
    adaptive_step  = 0.95,
    PBC_flag="hdim_2", min_h2=0, max_h2=3600) # 3600 is lon dims in imerg grid


# wenn 20 m/s = 51867
# wenn 50 m/s = 40164
# wenn 100 m/s = 39550
# 
# => nun frage was richtig ist....

# # merge and splits

# In[6]:


merges_splits = tobac.merge_split.merge_split_MEST(
    Tracks, dxy=dxy, distance=dxy, frame_len=0, # 1 timestamp away
    PBC_flag="hdim_2", min_h2=0, max_h2=3599
)
Tracks["track"] = merges_splits.feature_parent_track_id.data.astype(np.int64)

track_start_time = Tracks.groupby("track").time.min()
Tracks["time_track"] = Tracks.time - track_start_time[Tracks.track].to_numpy()


# In[7]:


#merges_splits.cell_ends_with_merge.sum(), merges_splits.cell_starts_with_split.sum()


# In[8]:


#merges_splits.track_child_cell_count.max(),Tracks.track.max(),Tracks.cell.max()


# In[9]:


#Tracks.columns


# ## add velo 

# In[10]:


Tracks = tobac.calculate_velocity(Tracks, method_distance="latlon")
#Tracks["v"].describe()


# ## add rain amount

# In[11]:


Tracks["rain_amount"] =  (3 * Tracks["mean_precip_cell"] * Tracks["area_cell"] )  # mm m2 



# # save raw Tracks

# In[12]:


# if saveoutputs: 
#     # save features
#     Tracks.to_hdf(
#         os.path.join(savedir, f"all_tracks_{model}_{timeperiod}_{year}.h5"),
#         key='table', mode='w'
#     )


# # filter
# qc and long  lived filter

# In[18]:


# to keep logic from 53 
models = ["ICON"]
timeperiods = ["FULL"]
ds = {}
ds["ICON"] = {}
ds["ICON"]["FULL"] = Tracks


# ### qc size filter

# In[19]:


# filter 
sizefilter = 2

ds_valid = {}

# for diagnosics 
diag = {model: {} for model in models}
all_max_sizes = {}

for model in models:
    ds_valid[model] = {}
    for timeperiod in timeperiods:
        
        Tracks = ds[model][timeperiod].copy()

        # exclude tracks that never exceed sizefilter pixels
        tracks_max_size = Tracks.groupby("track")["num_cell"].max()
        bad_size_tracks = tracks_max_size[tracks_max_size <= sizefilter].index
       
         # filter
        bad_tracks = bad_size_tracks #.union(bad_velocity_tracks).union(bad_lifetime_tracks)
        ds_valid[model][timeperiod] = Tracks[~Tracks["track"].isin(bad_tracks)]


# In[ ]:


# save valid 
# skipped


# ### long lifed filter

# In[20]:


hourfilter = "12"
ds_long = {}
for model in models:
    ds_long[model] = {}
    for timeperiod in timeperiods:
        
        Tracks = ds_valid[model][timeperiod]
        
        lifetime = Tracks.groupby("track")["time_track"].max()
        long_lived_cells = lifetime[lifetime >= pd.Timedelta(f"{hourfilter}h")].index
        ds_long[model][timeperiod] = Tracks[Tracks["track"].isin(long_lived_cells)]
        
    


# ### save filtered & valid

# In[24]:


for model in models:
    for timeperiod in timeperiods:
        outpath = os.path.join(savedir_filtered, f"all_tracks_filtered_{model}_{timeperiod}_{year}.h5")
        ds_long[model][timeperiod].to_hdf(
            outpath,
            key='table', mode='w'
        )
        print(f"saved to {outpath}")

