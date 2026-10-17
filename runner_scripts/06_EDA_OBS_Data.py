#!/usr/bin/env python
# coding: utf-8

# # EDA OBS Data
# goals
# - count how many pixel miss per timestamp (in mean image)
# 
# 
# goal outputs: => in nbook 07!
# - plot with timeseires how many pixels are NAN
# - global map with nan counts (per pixel)
# - ggf that map but per month or so
# 
# - count missing timestamps from outputprint
# 
# this nbook: 
# - loads/ calculates 3hourly mean images
# - counts nan and bad pixel values
# - saves the map  and summary of that in EDA_OBS/
# - for preicp, tb, and iwp
# - ALSO: use the putput print of this nbook to access how many timestamps are missing completely
# 
# 
# 
# infos: 
# - in IMERG missing values are -9999.9 or -9999 (huffmann 2023: https://arthurhou.pps.eosdis.nasa.gov/Documents/IMERG_TechnicalDocumentation_final.pdf)
# - in NAsa Tb and CCIC missing values ate Nan

# In[1]:


import sys
sys.path.append("../tools")

import handle_OBS_data as ob


import xarray as xr

# plotting
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import seaborn as sns

import os


# for dat creation 
import pandas as pd

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


# # define putput path

# In[2]:


output_dir = "../output/EDA_OBS/"

os.makedirs(output_dir, exist_ok=True)


# In[3]:


#print(f"sys.argv: {sys.argv}")


# # inputs 

# In[4]:


startdate, enddate = sys.argv[1].split()
# startdate = "2023-06-14-00"
# enddate =  "2023-06-14-21"

dates = ob.create_3h_timestamps(startdate, enddate)
print(f"dates that will be loaded {dates}")


# # load data 

# In[5]:


precip = ob.mean_precip_images_multiple_mean_images(dates)
precip
print("precip loaded")


# In[6]:


tb = ob.mean_tb_images_multiple_mean_images(dates)
tb
print("tb laoded")


# In[7]:


iwp = ob.mean_iwp_images_multiple_mean_images(dates)
iwp
print("iwp loaded")


# In[8]:


# da = iwp.compute()  # your DataArray

# print("min:  ", float(da.min()))
# print("max:  ", float(da.max()))
# print("NaN count:     ", int(np.isnan(da).sum()))
# print("-9999 count:   ", int((da == -9999).sum()))
# print("negative count:", int((da < 0).sum()))
# print("zero count:    ", int((da == 0).sum()))
# print("total pixels:  ", da.size)


# # count missing pixels PIXELwise

# In[9]:


def count_nan_and_badvalue_pixelwise(ds, badvalue=-9999):
    stacked = xr.concat(ds, dim='time') # stack iamges along time dim
    stacked = stacked.astype("float32")
    stacked.attrs.clear()
    
    missing = np.isnan(stacked) | (stacked <= badvalue)

    
    nan_map = missing.sum(dim = "time").compute()

    # ####################

    # import psutil, os, time

    # process = psutil.Process(os.getpid())
    
    # def print_mem(stage):
    #     mem = process.memory_info().rss / (1024**3)
    #     print(f"{stage}: {mem:.2f} GB")
    
    # print_mem("before concat")
    
    # stacked = xr.concat(ds, dim='time') # stack iamges along time dim
    # stacked = stacked.astype("float32")
    # stacked.attrs.clear()
    
    # missing = np.isnan(stacked) | (stacked <= badvalue)

    
    # print_mem("after concat (lazy)")
    
    # nan_map = missing.sum(dim = "time").compute()
    
    # print_mem("after nan_map plus compute")

    # # counts per timestamp
    # nan_per_time = np.isnan(stacked).sum(dim=[d for d in stacked.dims if d != 'time']).compute()

    # print_mem("after nan_per_time compute")

    # ####################
    
    # counts per timestamp
    nan_per_time = np.isnan(stacked).sum(dim=[d for d in stacked.dims if d != 'time']).compute()


    # combine the two pixelwise maps into one Dataset
    maps_ds = xr.Dataset({
        "nan": nan_map
    })
    
    # combine the two time series into one Dataset
    counts_ds = xr.Dataset({
        "nan": nan_per_time
    })
        
    return maps_ds, counts_ds


# In[10]:


import psutil
import os

process = psutil.Process(os.getpid())
mem_gb = process.memory_info().rss / (1024**3)

print(f"Current memory usage: {mem_gb:.2f} GB")


# In[11]:


# imerg precip 
nan_map_precip,nan_precip= count_nan_and_badvalue_pixelwise(precip)
print("precip map and count calculated")

nan_map_precip.to_netcdf(os.path.join(output_dir, f"precip_quality_maps_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})

nan_precip.to_netcdf(os.path.join(output_dir,f"precip_quality_counts_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})
print("precip map and count saved")


# In[12]:


# nassa t b
nan_map_tb,nan_tb= count_nan_and_badvalue_pixelwise(tb)
print("tb map and count calculated")

nan_map_tb.to_netcdf(os.path.join(output_dir, f"tb_quality_maps_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})

nan_tb.to_netcdf(os.path.join(output_dir,f"tb_quality_counts_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})
print("tb map and count saved")


# In[13]:


# iwp
nan_map_iwp,nan_iwp= count_nan_and_badvalue_pixelwise(iwp)
print("iwp map and count calculated")

nan_map_iwp.to_netcdf(os.path.join(output_dir, f"iwp_quality_maps_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})

nan_iwp.to_netcdf(os.path.join(output_dir,f"iwp_quality_counts_{startdate}_till_{enddate}.nc"), encoding={
    "nan": {"dtype": "int32","zlib": True, "complevel": 4}
})
print("iwp map and count saved")

