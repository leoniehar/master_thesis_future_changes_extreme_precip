#!/usr/bin/env python
# coding: utf-8

# # nbook to create a dataframe of cell properties 
# - use track ids as basis!
# - bascially: converting cell feature properties to life tim eintegrated cell properties

# # load packages 

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


import sys

import tobac


# # load data

# In[ ]:


inputdir = "../output/linking/filtered"
models = ["ICON"]

#timeperiods = [str(y) for y in range(2021, 2022)] # 2050 for full ! 

if "launcher" in sys.argv[0]: 
    timeperiods =  [str(y) for y in range(2045, 2050)] # 2050 for full ! 

else: 
    timeperiods = sys.argv[1]



# In[ ]:


## load tracks
ds = {}
for model in models: 
    ds[model] = {}
    for timeperiod in timeperiods: 
        file = os.path.join(inputdir,f"all_tracks_filtered_{model}_FULL_{timeperiod}.h5")
        Tracks = pd.read_hdf(file, key='table') 
        Tracks = Tracks.rename(columns={
            "min_tb": "min_tb_anvil",
            "mean_iwp": "mean_iwp_anvil",
            "max_iwp": "max_iwp_anvil",
            "total_iwp":"total_iwp_anvil",
            #"rain_amount": "rain_amount_cell"
        })
        ds[model][timeperiod] = Tracks.reset_index()


# In[ ]:


#ds["ICON"]["2021"]


# ## arguements

# In[ ]:


savedir = Path("../output/final_dataframes/FULL")
savedir.mkdir(parents=True, exist_ok=True)

domain_area_m2 = 255032272355328.0


# # def functions

# In[ ]:


def add_min_distance(df, exclude_mask_function, group_col="frame",
                      lat_col="latitude", lon_col="longitude"):
    """
    General minimum-distance-to-other-feature operator.
    """
    tmp = []

    for _, df_one_frame in df.groupby(group_col, sort=False):
        lat_arr = df_one_frame[lat_col].values
        lon_arr = df_one_frame[lon_col].values
        n = len(df_one_frame)
        result = np.full(n, np.nan)

        for i in range(n):
            mask = exclude_mask_function(df_one_frame, i)
            if not mask.any():
                continue  # C(i) empty -> leave as NaN (e.g. lone feature in frame)
            distances = tobac.analysis.spatial.haversine(lat_arr[i], lon_arr[i], lat_arr[mask], lon_arr[mask])
            result[i] = distances.min()

        tmp.append(pd.Series(result, index=df_one_frame.index))

    return pd.concat(tmp).reindex(df.index)

    
def exclude_none(df, i):
    not_self = np.arange(len(df)) != i
    return not_self
def exclude_sisters(df,i):
    not_self = np.arange(len(df)) != i
    not_sister = df["feature_anvil"].values != df["feature_anvil"].values[i]
    return not_self & not_sister


# # add cell feature properties not yet present but needed
# 
# 

# In[ ]:


for model in models: 
    for timeperiod in timeperiods: 
        Tracks = ds[model][timeperiod]


        # new rain amount (again in pendegrass normlaization
        Tracks = Tracks.drop(columns=["rain_amount"], errors="ignore")
        Tracks["rain_amount_cell"]= Tracks["mean_precip_cell"] * Tracks["area_cell"] 
        
        # sister cells = cells under the same anvil
        # n sister cells => number of sister cells at a given time excluding the cell itself
        Tracks["n_sister_cells"] = (Tracks.groupby(["frame", "feature_anvil"])["track"].transform("nunique") - 1)
        
        # fraction of rain from cell falling in anvil
        #Tracks["frac_rain_cell_rain_anvil"] = Tracks["total_precip_cell"] / Tracks["total_precip_anvil"]
        
        # min distacne to non sister
        Tracks["min_dist_nonsister_cell_km"] = add_min_distance(Tracks,exclude_sisters)
        
        # nearest neightbour 
        Tracks["min_dist_cell_km"] = add_min_distance(Tracks,exclude_none)
        #tobac.analysis.spatial.calculate_nearestneighbordistance(Tracks, method_distance="latlon")

        ##################################
        ##################################
        # anvil related
        Tracks["rain_amount_anvil"]= Tracks["mean_precip_anvil"] * Tracks["area_anvil"]  # as pendergrass total rain normalized to mm/h

        # n children
        Tracks["n_children_anvil"] = Tracks.groupby(["frame", "feature_anvil"])["track"].transform("nunique") 

        #  iwp amount (aka total iwp) 
        Tracks["iwp_amount_anvil"]= Tracks["mean_iwp_anvil"] * Tracks["area_anvil"] 





        
        
        # PE try  Functioniert (aber zu kleine werte)
        # sort to guarantee correct frame order within each track before diffing
        # Tracks = Tracks.sort_values(["track", "frame"])

        # # raw change in mean_iwp between consecutive timesteps along each cell's track
        # Tracks["d_iwp"] = Tracks.groupby("track")["mean_iwp_anvil"].diff()
        
        # # convert to a rate: kg/m^2 per hour (3-hourly steps -> divide by 3)
        # Tracks["iwp_dt"] = Tracks["d_iwp"] / 3# kg/m2 /h

        # # def P and iwp tendency
        # P = Tracks["mean_precip_anvil"] # mm/h
        # Tracks["iwp_dt_positive"] = Tracks["iwp_dt"].clip(lower=0)

        

        # # actual calc
        # Tracks["PE_cell"] = 100*P/( P + Tracks["iwp_dt_positive"])

        ########################################
        ######################################
        
        # assign to ds
        ds[model][timeperiod] = Tracks

       
        


# In[ ]:


Tracks.columns


# # cretae dataframe based on cell ids

# In[ ]:


cellprops ={}
for model in models: 
    cellprops[model] = {}
    for timeperiod in timeperiods: 
        Tracks = ds[model][timeperiod]
        
        cellprops[model][timeperiod] = Tracks.groupby("track").agg(
        
            # precip intensity
            mean_precip_cell_mean=("mean_precip_cell", "mean"),   # lifetime-averaged mean precip rate
            max_precip_cell_max=("max_precip_cell", "max"),       # max of max precip rate over lifetime
            total_precip_cell_mean =("total_precip_cell", "mean"), # avergae total rain rate
            rain_amount_cell_sum =("rain_amount_cell", "sum"), 
        
            # diagostics? 
            lifetime_cell= ("time_track", "max"),
            area_cell_mean          = ("area_cell", "mean"),
            d_eq_cell_mean          = ("d_eq_cell", "mean"),
            d_eq_cell_max  = ("d_eq_cell", "max"),
            velo_cell_mean = ("v","mean"),
        
        
            # aggregation 
            n_sister_cells_max  = ("n_sister_cells", "max"),
            n_sister_cells_mean  = ("n_sister_cells", "mean"),
        
             
            #min_dist_nonsister_cell_km_min = ("min_dist_nonsister_cell_km","min"),
            min_dist_nonsister_cell_km_mean = ("min_dist_nonsister_cell_km","mean"),


            #min_dist_cell_km_min = ("min_dist_cell_km","min"),
            min_dist_cell_km_mean = ("min_dist_cell_km","mean"),
          
            #mean_frac_anvil_rain = ("frac_rain_cell_rain_anvil", "mean") #leave out
            # lost 
            #PE_cell_mean = ("PE_cell","mean"),
            
            ############################
            # related to anvil duplicates
            mean_precip_anvil_mean = ('mean_precip_anvil', "mean"),
            rain_amount_anvil_sum =("rain_amount_anvil","sum"),
          
            mean_iwp_anvil_mean = ('mean_iwp_anvil', "mean"),
            max_iwp_anvil_max = ("max_iwp_anvil","max"),
            
            total_iwp_anvil_mean = ('total_iwp_anvil', "mean"),
            iwp_amount_anvil_sum =("iwp_amount_anvil","sum"),

            
                
            area_anvil_mean          = ("area_anvil", "mean"),
            d_eq_anvil_mean          = ("d_eq_anvil", "mean"),
            d_eq_anvil_max          = ("d_eq_anvil", "max"),
            
            min_tb_anvil_min =  ("min_tb_anvil", "min"),
            
            n_children_anvil_mean = ("n_children_anvil","mean"),

            time = ("time","min"), # starttime


            #########
            # env T 
            tas_cell_mean =("tas_cell","mean")


            ).reset_index()

        
        cellprops[model][timeperiod]["lifetime_cell"] = (cellprops[model][timeperiod]["lifetime_cell"].dt.total_seconds() / 3600)

        # storm integrated PE 

        # total summed fluxed during lifetime
        # tmp = Tracks.groupby("track").agg(
        #     P_sum_a = ("mean_precip_anvil", "mean"),
        #     iwp_dt_positive_sum_a = ("iwp_dt_positive", "sum")).reset_index()
        
        # # storm-integrated PE
        # cellprops[model][timeperiod]["PE_anvil_lifetime"] = ( 100 * tmp["P_sum_a"]/ (tmp["P_sum_a"] + tmp["iwp_dt_positive_sum_a"]))
                    


# => than maybe just add a anvilfeature dataframe=> all anvilfeatures associated to at least one cell for each timestamp
# => use anvil features for efficiency aussagen und aber diskueiren, dass es keine lif etime aggregated propertiey ist wie die restlichen => require anvil linking!

# # Cretae feature datasets 

# In[ ]:


columns_tracks = cellprops["ICON"][timeperiods[0]].columns    # aggregated (track-level)
columns_features = ds["ICON"][timeperiods[0]].columns          # raw (feature-level)




# ### anvil feature dataset

# In[ ]:


# raw anvil columns from ds
anvil_cols_raw = [c for c in columns_features if "anvil" in c.lower()]
anvil_cols_used= ["time","feature_anvil"]+[c for c in anvil_cols_raw if any(col.startswith(c) for col in columns_tracks)] 



anvilfeatures ={}
for model in models: 
    anvilfeatures[model] = {}
    for timeperiod in timeperiods: 
        Tracks = ds[model][timeperiod]
        tmp = (Tracks.drop_duplicates(subset=['time', 'feature_anvil'], keep='first')[anvil_cols_used].reset_index(drop=True))

        # convective rain amount
        convectiverain = Tracks.groupby(['time', 'feature_anvil'])['rain_amount_cell'].sum().reset_index().rename(columns={'rain_amount_cell': 'convective_rain_amount_anvil'})

        # merge on the composite key -> guarantees correct row alignment
        tmp = tmp.merge(convectiverain, on=["time", "feature_anvil"], how="left")
        anvilfeatures[model][timeperiod] = tmp


# ### cell features 
# select relevant cell feature columns from ds

# In[ ]:


cell_cols_raw = [c for c in columns_features if "cell" in c.lower()]
cell_cols_used= ["time","feature"] +[c for c in cell_cols_raw if any(col.startswith(c) for col in columns_tracks)] 


       
cellfeatures ={}
for model in models: 
    cellfeatures[model] = {}
    for timeperiod in timeperiods: 
        cellfeatures[model][timeperiod] = ds[model][timeperiod][cell_cols_used]
        
    


# # Save cell tracks, cell features and anvil features

# In[ ]:


for model in models:
    for timeperiod in timeperiods:
        # cell features
        cellfeatures[model][timeperiod].to_hdf(
            os.path.join(savedir, f"cell_features_{model}_{timeperiod}.h5"),
            key='table', mode='w')
        # anvil features
        anvilfeatures[model][timeperiod].to_hdf(os.path.join(savedir, f"anvil_features_{model}_{timeperiod}.h5"),
            key='table', mode='w')
        # cell tracks
        cellprops[model][timeperiod].to_hdf(os.path.join(savedir, f"cell_tracks_{model}_{timeperiod}.h5"),
            key='table', mode='w')
        
        

