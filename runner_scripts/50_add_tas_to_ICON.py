#!/usr/bin/env python
# coding: utf-8

# # add tas env variable to ICON features 
# - only for 30 yrs dataset needed! 
# - tried on June 2023 with ntasks = 128 => completed in null komma nix

# In[1]:


import warnings

# ignore general categories
for cat in [FutureWarning, RuntimeWarning, UserWarning]:
    warnings.filterwarnings("ignore", category=cat)

# ignore specific repeated messages
for msg in [
    "pyproj unable to set PROJ database path",
    "As of v1.6.0, segmentation with time length 1",
    "Using DEFAULT_SPHERICAL_EARTH_RADIUS",
    "your performance may suffer as PyTables will pickle object types that it cannot"
]:
    warnings.filterwarnings("ignore", message=msg)


import numpy as np
import xarray as xr
import os
import pandas as pd


from pathlib import Path

import glob

import sys

sys.path.append("../tools")
#from defs_application import bad_timesteps
import handle_ICON_data as ic


# In[2]:


if "launcher" in sys.argv[0]: 
    interactive =True
    saveoutputfiles = False
    date = "2046-12-17-0900" #"2023-06-06-1800"
else: 
    interactive = False
    saveoutputfiles= True
    date = sys.argv[1]

    


# In[3]:


inputdir = Path(f"../output/apply_seg/apply_ICON/FULL/cell_features_combined")
filename = f"cell_features_combined_anvil_detectthres225_seg241_cell_detectthres10_seg10_{date}"

if saveoutputfiles: 
    savedir = inputdir.parent / (inputdir.name + "_envfeatures")

    #savedir = Path("/scratch/b/b383071/cell_features_combined_env_features")
    
    savedir.mkdir(parents=True, exist_ok=True)


# ## Load features (output from segmentation)

# In[4]:


file = f'{inputdir}/{filename}.h5'
data = pd.read_hdf(file, key='table')  
data = data.reset_index(drop=True)
#data


# ## Load icon

# In[ ]:


# data selection
zoom = 5 
vlist = ["tas", "crs"]

# load data
dataset = ic.open_ngc4008(zoom = zoom) 

# select timestamp and variables
dataset = ic.select_time(dataset, date)
dataset = ic.select_vars(dataset, vlist)


dataset


# In[ ]:


data


# In[ ]:


# import healpy as hp
# print(dataset.crs.attrs)

# nside = 2**zoom
# npix = 12 * nside**2

# # Approximate angular resolution (pixel size) in degrees
# resolution_deg = np.sqrt(4 * np.pi / npix) * (180 / np.pi)

# # Approximate resolution in km (at Earth's surface, R ≈ 6371 km)
# R_earth = 6371
# resolution_km = np.sqrt(4 * np.pi * R_earth**2 / npix)

# print(f"nside: {nside}")
# print(f"npix: {npix}")
# print(f"approx resolution: {resolution_deg:.3f} degrees")
# print(f"approx resolution: {resolution_km:.1f} km")

# # healpy page
# NSIDE = 32
# print(
#     "Approximate resolution at NSIDE {} is {:.2} deg".format(
#         NSIDE, hp.nside2resol(NSIDE, arcmin=True) / 60
#     )
# )


# ## determine tas at features and as tas_env 

# In[ ]:


def colocate_tas_at_cell_centroids(cells_df, dataset, zoom=5, var="tas"):
    """
    Look up 2m temperature at cell centroids directly on HEALPix grid.
    Avoids lossy regridding to lat/lon.
    
    Parameters
    ----------
    cells_df : pd.DataFrame
        Cell feature dataframe with latitude_cell, longitude_cell columns
    dataset : xr.Dataset
        ICON ngc4008 dataset (HEALPix, already time-selected)
    zoom : int
        HEALPix zoom level (nside = 2**zoom)
    var : str
        Variable name to look up
    
    Returns
    -------
    cells_df : pd.DataFrame
        Input dataframe with new column f"{var}_cell"
    """
    import healpy as hp
    nside = 2 ** zoom
    
    # Get HEALPix pixel indices for each cell centroid
    # healpy expects co-latitude (theta) and longitude (phi) in radians
    lats = cells_df["latitude_cell"].values
    lons = cells_df["longitude_cell"].values % 360  # modulo => so that 0-360 lons
    
    theta = np.radians(90 - lats)   # colatitude
    phi   = np.radians(lons)
    
    pix_ids = hp.ang2pix(nside, theta, phi, nest=True)  # nest=True for ICON
    
    # Extract tas values at those pixels
    tas_vals = dataset[var].squeeze().values[pix_ids]
    #tas_vals = dataset[var].values[pix_ids]
    
    cells_df = cells_df.copy()
    cells_df[f"{var}_cell"] = tas_vals
    
    return cells_df


# In[ ]:


cells_with_tas = colocate_tas_at_cell_centroids(data, dataset, zoom=zoom)
#cells_with_tas


# # save features

# In[ ]:


# save features
if saveoutputfiles:
    cells_with_tas.to_hdf(
        savedir / f'{filename}-envfeatures.h5',
        key='table', mode='w'
    )
    
    print(f'cell features combined with anvil properties saved for {date}')



# # resample to IMERG AND Plot (only out of curiosity, to check if data is ok)

# In[ ]:


## colocate the ICON data with OBS
# resample to Imerg grid
if interactive: 
    tas= ic.resample_to_lon_lat(dataset, "tas", zoom= zoom,to_imerg = True)


# In[ ]:


if interactive: 
    # invert colorbar! and set scaling correct
    def summarized_domain_plot(tas, title, domain=[-180,180,-30,30],
                               tas_vmin=200, tas_vmax=300):
        import seaborn as sns
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import plots_mapping as pm
        
        sns.set_context("talk")
        fig, ax = plt.subplots(
            1, 1,
            figsize=(12, 7),
            subplot_kw={"projection": ccrs.PlateCarree()},
            constrained_layout=True
        )
    
        ax = pm.domain_plot_tas(tas, domain=domain, left_grid_label=True, bottom_grid_label=True,
                       title=r"'tas' zoom 5 ($T_{\text{env}}$)",
                       vmin=tas_vmin, vmax=tas_vmax,
                       fig=fig, ax=ax,shrink = 0.3)
        
    
        fig.suptitle(title, fontweight="bold")
    
        return fig
        
    tas.attrs["short_name"] = r"$T_{\text{env}}$"
    
    zoom5 = summarized_domain_plot(tas = tas, title = "", domain=[-180,180,-30,30],
                                   tas_vmin=270, tas_vmax=320)

    zoom5.savefig(f"../output/plots/tas_input_image_example_{date}.pdf")

