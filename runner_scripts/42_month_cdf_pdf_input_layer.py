#!/usr/bin/env python
# coding: utf-8

# # plot CDF and/or PDF of input layer
# 
# # !! execute with runner_42 !!
# 
# ## (started as duplicate of 41) 
# - calculate histgram values per timestamp
# - save as netcdf
# - => in 43: load and plot

# In[1]:


import sys
sys.path.append("../tools")

import handle_OBS_data
import handle_ICON_data as ic
import inputlayer


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

from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


# ### styling parameter

# In[2]:


# color_precip_icon = "dodgerblue"
# color_precip_obs= "darkblue"

# color_tb_icon = "orangered"
# color_tb_obs = "firebrick"


from defs_application import *


# # inputs

# In[3]:


# date = pd.date_range("2023-06-06", periods=8, freq="3h").strftime("%Y-%m-%d-%H%M").tolist()
# date
import sys 

#dates =   #

if "launcher" in sys.argv[0]: 
    dates = ["2023-12-27-0000"]  
    outputdir =Path("../output/cdf/datatry/")
    interactive =True
else: 
    dates = [sys.argv[1]] 
    outputdir =Path("../output/cdf/data/")
    interactive = False


# In[4]:


# create main directory
outputdir.mkdir(parents=True, exist_ok=True)


# # define functions

# In[5]:


# def open_icon_images(dateslist):
#     icon_precip = []
#     icon_tb = []
#     icon_iwp = []
    
#     zoom = 9
#     dataset_total = ic.open_ngc4008(zoom=zoom)
        
#     for date in dateslist:  # fix: was using global `dates` instead of argument
#         vlist = ["pr", "crs", "rlut", "clivi", "qsvi", "qgvi"]
        
#         dataset = ic.select_time(dataset_total, date)
#         dataset = ic.select_vars(dataset, vlist)
        
#         dataset = ic.add_precip_tot_rate(dataset)
#         dataset = ic.add_tb_11(dataset)
#         dataset = ic.add_iwp(dataset)  # check your actual function name
        
#         precip = ic.resample_to_lon_lat(dataset, "rain_tot_rate", to_imerg=True)
#         tb    = ic.resample_to_lon_lat(dataset, "tb_11",          to_imerg=True)
#         iwp   = ic.resample_to_lon_lat(dataset, "iwp",            to_imerg=True)
        
#         icon_precip.append(precip)
#         icon_tb.append(tb)
#         icon_iwp.append(iwp)
    
#     precip_icon = xr.concat(icon_precip, dim="time").compute()
#     tb_icon     = xr.concat(icon_tb,     dim="time").compute()
#     iwp_icon    = xr.concat(icon_iwp,    dim="time").compute()
    
#     return precip_icon, tb_icon, iwp_icon
    
# def open_rlut_icon(dateslist):
#     icon_rlut = []
#     icon_tf = []

#     zoom = 9
#     dataset_total = ic.open_ngc4008(zoom=zoom)
        
#     for date in dateslist:  
#         vlist = ["crs", "rlut"]
        
#         dataset = ic.select_time(dataset_total, date)
#         dataset = ic.select_vars(dataset, vlist)
        
      
#         dataset = ic.add_tf(dataset)
        
         
#         rlut = ic.resample_to_lon_lat(dataset, "rlut", to_imerg=True)
#         tf = ic.resample_to_lon_lat(dataset, "tf", to_imerg=True)
        

#         icon_rlut.append(rlut)
#         icon_tf.append(tf)


    
#     icon_rlut = xr.concat(icon_rlut, dim="time").compute()
#     icon_tf = xr.concat(icon_tf, dim="time").compute()

#     return icon_rlut, icon_tf


# ### genral 

# In[6]:


# # for binning

# def log_bins(low=-2, high=2, n=60):
#     return np.logspace(low, high, n)

# def linear_bins(*arrays, n=80, pad=1):
#     lo = min(np.nanmin(a.values) for a in arrays)
#     hi = max(np.nanmax(a.values) for a in arrays) 
#     return np.linspace(lo - pad, hi + pad, n)

# # maybe try? and check lol
# def pendergrass_bins(low_mmhr=0.03/24, high_mmhr=300, pct=0.07):
#     """
#     Logarithmic bins with fixed percentage spacing (default 7% like Pendergrass)
#     low_mmhr: dry threshold (0.03 mm/day converted to mm/hr)
#     """
#     edges = [low_mmhr]
#     while edges[-1] < high_mmhr:
#         edges.append(edges[-1] * (1 + pct))
#     return np.array(edges)


# #### counts 

# In[7]:


# def compute_pdf(
#     data_list,
#     bins,
#     labels,
#     filter_positive=False,
# ):
#     """
#     Compute per-timestep histograms for each dataset.
#     All datasets must share the same time axis.
#     Returns an xarray.Dataset ready to save as netCDF.
#     """
#     bin_centers = 0.5 * (bins[:-1] + bins[1:])
    
#     data_vars = {}

#     for data, label in zip(data_list, labels):
#         hist_list = []
#         for t in data.time:
#             values = data.sel(time=t).values.flatten()
#             values = values[~np.isnan(values)]
#             if filter_positive:
#                 values = values[values > 0]
#             counts, _ = np.histogram(values, bins=bins, density=False)
#             hist_list.append(counts)

#         time_coord = data.time.values

#         safe = label.replace(" ", "_")
#         data_vars[f"counts_{safe}"] = xr.DataArray(
#             np.stack(hist_list, axis=0),          # (time, bin)
#             dims=["time", "bin_center"],
#             attrs={"label": label, "filter_positive": str(filter_positive)},
#         )

#     ds = xr.Dataset(
#         data_vars,
#         coords={
#             "time":       time_coord,
#             "bin_center": bin_centers,
#             "bin_left":   ("bin_center", bins[:-1]),
#             "bin_right":  ("bin_center", bins[1:]),
#         },
#         attrs={"filter_positive": str(filter_positive)},
#     )
#     return ds


# def calc_area_weights(da):
#     """
#     Compute fractional area weights (a_grid / a_total) for a regular lat/lon grid.
#     Input: xarray DataArray with lat and lon dims.
#     """
#     cos_lat = np.cos(np.deg2rad(da.latitude))  # (nlat,)
#     weights_2d = cos_lat * xr.ones_like(da.longitude)  
#     weights_2d = weights_2d / weights_2d.sum()  # a_grid / a_total
#     return weights_2d
    

# def compute_amount_distribution(
#     data_list,
#     bins,
#     labels,
#     filter_positive=False,
#     area_weights=None,
# ):
#     '''
#     rain amount distribution like pendergrass 2014  Two modes of change (A1 Appendix)
#     '''
#     bin_centers = 0.5 * (bins[:-1] + bins[1:])
#     delta_lnR = np.log(bins[1:]) - np.log(bins[:-1])
    
#     data_vars = {}

#     for data, label in zip(data_list, labels):
#         AR_list = []

#         if area_weights is not None:
#             w = area_weights.values.flatten() # Agrid/ages (computed before) 

#         for t in data.time:
#             values = data.sel(time=t).values.flatten()
#             weights = w.copy() if area_weights is not None else np.ones_like(values)
            
#             valid = ~np.isnan(values)
#             if filter_positive: # i dont do it
#                 valid &= (values > 0)
            
#             values  = values[valid]
#             weights = weights[valid]


#             # if weights.sum() > 0: # normalize area weights to the "valid" area excluding the dry pixels
#             #     weights = weights / weights.sum()

#             amount, _ = np.histogram(values, bins=bins, weights=weights * values) # sum gridpoints
#             AR_list.append(amount / delta_lnR) # 1/ delta lnR

#         time_coord = data.time.values

#         safe = label.replace(" ", "_")
#         data_vars[f"contri_{safe}"] = xr.DataArray(
#             np.stack(AR_list, axis=0),
#             dims=["time", "bin_center"],
#             attrs={"label": label, "units": "mm h-1",
#                    "description": "Pendergrass 2014 rain amount distribution"},
#         )

#     ds = xr.Dataset(
#         data_vars,
#         coords={
#             "time":       time_coord,
#             "bin_center": bin_centers,
#             "bin_left":   ("bin_center", bins[:-1]),
#             "bin_right":  ("bin_center", bins[1:]),
#         },
#     )
#     return ds

    

# # def add_contribution(ds):
# #     """
# #     Add counts * bin_center for each counts_* variable in the dataset
# #     normalized by bin width
# #     """
# #     delta_log_r = np.log(ds["bin_right"].values) - np.log(ds["bin_left"].values)  # constant for log-spaced bins
# #     delta_log_r = xr.DataArray(delta_log_r, dims=["bin_center"])

    
# #     for var in list(ds.data_vars):
# #         if var.startswith("counts_"):
# #             suffix = var[len("counts_"):]
# #             ds[f"contri_{suffix}"] = ds[var] * ds["bin_center"] / delta_log_r # ds[var] * ds["bin_center"]
# #             ds[f"contri_{suffix}"].attrs = {
# #                 "long_name": f"Rain amount distribution for {suffix}",
# #                 "units": "mm h-1",
# #                 "description": "counts/(binspacing in log space* rainrate at bin_center)",
# #             }
# #     return ds
# def keep_only(ds, prefix):
#     drop_vars = [v for v in ds.data_vars if not v.startswith(prefix)]
#     return ds.drop_vars(drop_vars)
    
# # def get_cdf(ds):
# #     for var in list(ds.data_vars):
# #         if var.startswith("counts_"):
# #             suffix = var[len("counts_"):]
# #             total = ds[var].sum(dim="bin_center")
# #             ds[f"cdf_{suffix}"] = ds[var].cumsum(dim="bin_center") / total
# #             ds[f"cdf_{suffix}"].attrs = {
# #                 **ds[var].attrs,
# #                 "description": "cumulative distribution function",
# #             }
# #     ds = keep_only(ds,"cdf")
# #     return ds

# def get_cdf(ds):
#     original_vars = list(ds.data_vars) 
#     for var in original_vars:
#         total = ds[var].sum(dim="bin_center")
#         ds[f"cdf_{var}"] = ds[var].cumsum(dim="bin_center") / total
#         ds[f"cdf_{var}"].attrs = {
#             **ds[var].attrs,
#             "description": "cumulative distribution function",
#         }
#     ds = keep_only(ds,"cdf")
#     return ds


# # Load data
# ### OBS data

# In[8]:


obs_mean_images= []
for date in dates:
    # load data
    precip = handle_OBS_data.load_calc_clean_mean_imerg(date, buffer = 30, min_images= 5)
    obs_mean_images.append(precip)

precip_obs = xr.concat(obs_mean_images, dim= "time").load()


# In[9]:


obs_mean_images= []
for date in dates:
    # load data
    tb = handle_OBS_data.load_calc_clean_mean_tb(date, buffer = 32, min_images= 5)
    obs_mean_images.append(tb)

tb_obs = xr.concat(obs_mean_images, dim= "time")
tb_obs =  handle_OBS_data.resample_grids(tb_obs,precip_obs).load()


# In[10]:


obs_mean_precip = []
obs_mean_images= []
for date in dates:
    # load data
    iwp = handle_OBS_data.load_calc_clean_mean_ccic(date, buffer = 32, min_images= 5)
    obs_mean_images.append(iwp)

iwp_obs = xr.concat(obs_mean_images, dim= "time")
iwp_obs = handle_OBS_data.resample_grids(iwp_obs,precip_obs).load()
iwp_obs


# ### ICON data (after OBS data!)

# In[11]:


# load
precip_icon, tb_icon, iwp_icon = ic.open_icon_images(dates)
rlut_icon, tf_icon = ic.open_rlut_icon(dates)


# # bins definition

# In[12]:


big = 80
small= 800

tb_bins_big = np.linspace(190,330,big)
tb_bins_small =  np.linspace(190,330,small)
precip_bins_big = inputlayer.log_bins(-2, 3, big)
precip_bins_small = inputlayer.log_bins(-2, 3, small)
iwp_bins_big = inputlayer.log_bins(low=-2, high=2, n = big)
iwp_bins_small = inputlayer.log_bins(low=-2, high=2, n = small)
rlut_bins_big = np.linspace(100,350,big)
rlut_bins_small = np.linspace(100,350,small)


precip_bins_big_pender = inputlayer.pendergrass_bins()


# In[13]:


iwp_bins_big


# # histgrams 

# In[14]:


date = dates[0]


# In[15]:


area_weights = inputlayer.calc_area_weights(tb_icon)  # same grid for all


# In[23]:


# tbs
hist_tb = inputlayer.compute_pdf([tb_icon, tb_obs,tf_icon], tb_bins_big, labels = ["tb_ICON","tb_OBS","tf_ICON"], filter_positive=False)
hist_tb.to_netcdf(os.path.join(outputdir,f"histograms_tb_{date}.nc"),engine="h5netcdf")

# precip
hist_precip = inputlayer.compute_pdf([precip_icon,precip_obs], precip_bins_big, labels = ["precip_ICON","precip_OBS"], filter_positive=False)
hist_precip.to_netcdf(os.path.join(outputdir,f"histograms_precip_{date}.nc"),engine="h5netcdf")

# add contribution
#hist_precip = add_contribution(hist_precip)
hist_precip_amount = inputlayer.compute_amount_distribution([precip_icon,precip_obs], precip_bins_big_pender , labels = ["precip_ICON","precip_OBS"], filter_positive=False,area_weights = area_weights)
#hist_precip = xr.merge([hist_precip, hist_precip_amount])
hist_precip_amount.to_netcdf(os.path.join(outputdir,f"histograms_precip_amount_{date}.nc"),engine="h5netcdf")





# iwp
hist_iwp = inputlayer.compute_pdf([iwp_icon,iwp_obs], iwp_bins_big, labels = ["iwp_ICON","iwp_OBS"], filter_positive=False)
# add contribution
#hist_iwp = add_contribution(hist_iwp)
hist_iwp_amount =inputlayer.compute_amount_distribution([iwp_icon,iwp_obs], iwp_bins_big, labels = ["iwp_ICON","iwp_OBS"], filter_positive=False,area_weights = area_weights)
hist_iwp = xr.merge([hist_iwp, hist_iwp_amount])
hist_iwp.to_netcdf(os.path.join(outputdir,f"histograms_iwp_{date}.nc"),engine="h5netcdf")

# # rlut 
hist_rlut= inputlayer.compute_pdf([rlut_icon], rlut_bins_big, labels = ["rlut_ICON"], filter_positive=False)
hist_rlut.to_netcdf(os.path.join(outputdir,f"histograms_rlut_{date}.nc"),engine="h5netcdf")
hist_rlut


# In[ ]:


hist_precip_amount


# # cdfs
# - re do histogramms BUT for small bins
# - add cdfs
# - delete unwanted variables

# In[26]:


# tbs
hist_tb = inputlayer.compute_pdf([tb_icon, tb_obs,tf_icon], tb_bins_small, labels = ["tb_ICON","tb_OBS","tf_ICON"], filter_positive=False)
# add cdf
hist_tb = inputlayer.get_cdf(hist_tb)
hist_tb.to_netcdf(os.path.join(outputdir,f"cdfs_tb_{date}.nc"),engine="h5netcdf")
hist_tb

# precip
hist_precip = inputlayer.compute_pdf([precip_icon,precip_obs], precip_bins_small, labels = ["precip_ICON","precip_OBS"], filter_positive=False)
#hist_precip = add_contribution(hist_precip)
hist_precip_amount = inputlayer.compute_amount_distribution([precip_icon,precip_obs], precip_bins_small, labels = ["precip_ICON","precip_OBS"], filter_positive=False,area_weights = area_weights)
hist_precip = xr.merge([hist_precip, hist_precip_amount])
# add cdf
hist_precip = inputlayer.get_cdf(hist_precip)
hist_precip.to_netcdf(os.path.join(outputdir,f"cdfs_precip_{date}.nc"),engine="h5netcdf")

# iwp
hist_iwp = inputlayer.compute_pdf([iwp_icon,iwp_obs], iwp_bins_small, labels = ["iwp_ICON","iwp_OBS"], filter_positive=False)
# add contribution
#hist_iwp = add_contribution(hist_iwp)
hist_iwp_amount =inputlayer.compute_amount_distribution([iwp_icon,iwp_obs], iwp_bins_small, labels = ["iwp_ICON","iwp_OBS"], filter_positive=False,area_weights = area_weights)
hist_iwp = xr.merge([hist_iwp, hist_iwp_amount])
# add cdf
hist_iwp = inputlayer.get_cdf(hist_iwp)
hist_iwp.to_netcdf(os.path.join(outputdir,f"cdfs_iwp_{date}.nc"),engine="h5netcdf")

# rlut 
hist_rlut= inputlayer.compute_pdf([rlut_icon], rlut_bins_small, labels = ["rlut_ICON"], filter_positive=False)
# add cdf
hist_rlut = inputlayer.get_cdf(hist_rlut)
hist_rlut.to_netcdf(os.path.join(outputdir,f"cdfs_rlut_{date}.nc"),engine="h5netcdf")
hist_rlut


