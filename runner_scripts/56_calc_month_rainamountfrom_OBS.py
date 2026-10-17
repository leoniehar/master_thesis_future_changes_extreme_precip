#!/usr/bin/env python
# coding: utf-8

# # short script to calculate rain amount/month 

# In[2]:


import numpy as np
import xarray as xr
import os
import pandas as pd

from pathlib import Path

# Import tobac itself:


import sys

#from tqdm.notebook import tqdm

import json

# import use_tobac

sys.path.append("../tools")
import handle_ICON_data as ic 
import handle_OBS_data as ob # for area weights
from defs_application import bad_timesteps

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



# In[9]:


if "launcher" in sys.argv[0]: 
    date = "2023-06-06-1800"
else: 
    date = sys.argv[1]

savedir = Path("../output/aux/rainamountsobs")
savedir.mkdir(parents=True, exist_ok=True)

outfile = savedir / f"rain_amounts_{date}.json"


#add a check if outfile exists if not filesdoesnotexist == True and then i add If filesdoesnotexist: before the followi ng cells
 
# Check if the file exists
if outfile.exists():
    filesdoesnotexist = False
else:
    filesdoesnotexist = True


# In[11]:


if filesdoesnotexist: 
    # get area weights 
    def calc_area_weights(da):
        """
        Compute fractional area weights (a_grid / a_total) for a regular lat/lon grid.
        Input: xarray DataArray with lat and lon dims.
        """
        cos_lat = np.cos(np.deg2rad(da.latitude))  # (nlat,)
        weights_2d = cos_lat * xr.ones_like(da.longitude)  
        weights_2d = weights_2d / weights_2d.sum()  # a_grid / a_total
        return weights_2d



# # OBS
# ### JUNE

# In[12]:


if filesdoesnotexist: 
    timeperiod = "JUNE"
    
    
    precip = ob.load_calc_clean_mean_imerg(date, buffer = 30, min_images= 5)
    
    area_weights = calc_area_weights(precip)
    
    # area-weighted domain mean rain rate (mm/h) (area weights sum up to 1
    weighted_mean = (precip * area_weights).sum().compute().item()
    rain_amount_june = weighted_mean * 3 # to mm


# #### save

# In[5]:


if filesdoesnotexist: 
    with open(outfile, "w") as f:
        json.dump({
            "timeperiod": timeperiod,
            "date": str(date),
            "rain_amount_mm": rain_amount_june
        }, f)

