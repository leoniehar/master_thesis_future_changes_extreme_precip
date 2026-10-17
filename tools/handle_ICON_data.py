def open_ngc4008(zoom=8):
    """Open the rechunked ICON ngc4008 3-hourly zarr at the given healpix zoom level."""
    import xarray as xr

    datasetpath = f"/work/kd1453/rechunked_ngc4008/ngc4008_PT3H_{zoom}.zarr"

    dataset = xr.open_zarr(datasetpath)
    dataset = dataset.chunk()  # keep same behaviour as original

    return dataset

###################################
####### calculate input variables #####
################################
# precipitation
def add_precip_tot_rate_day(dataset):
    """Add rain rate in mm day-1 ('rain_tot_rate_day') from 'pr' (kg m-2 s-1)."""
    dataset['rain_tot_rate_day'] = 3600 * 24 * ( dataset['pr'] )  # unit convetion to mm day-1
    
    dataset['rain_tot_rate_day'].attrs['units'] = 'mm day-1'
    
    dataset['rain_tot_rate_day'].attrs['long_name'] = 'rain rate'
    dataset['rain_tot_rate_day'].attrs['short_name'] = 'rain rate'
    return dataset


def add_precip_tot_rate(dataset):
    """Add rain rate in mm h-1 ('rain_tot_rate') from 'pr' (kg m-2 s-1)."""
    dataset['rain_tot_rate'] = 3600 * ( dataset['pr'] )  # unit convetion to mm day-1
    
    dataset['rain_tot_rate'].attrs['units'] = 'mm h-1'
    
    dataset['rain_tot_rate'].attrs['long_name'] = 'rain rate'
    dataset['rain_tot_rate'].attrs['short_name'] = 'rain rate'
    return dataset

# frozen water path
def add_iwp(dataset):
    """Add ice water path 'iwp' (kg m-2) = clivi + qsvi + qgvi."""
    dataset['iwp'] = dataset['clivi'] + dataset['qsvi'] + dataset["qgvi"]
    
    dataset['iwp'].attrs['units'] = 'kg m-2'
    
    dataset['iwp'].attrs['long_name'] = 'Ice water path' # vertically integrated frozem water
    dataset['iwp'].attrs['short_name'] = 'IWP'
    return dataset


# Tb 
def get_tb(olr):
    """
    from https://tobac.readthedocs.io/en/latest/examples/Example_ICON_MCS_tracking/Example_ICON_MCS_tracking.html
    
    This function converts outgoing longwave radiation to brightness temperatures.
    11 micron brightness temperature (BT) 

    Args:
        olr(xr.DataArray or numpy array): 2D field of model output with OLR

    Returns:
        tb(xr.DataArray or numpy array): 2D field with estimated brightness temperatures
    """
    # constants
    aa = 1.228
    bb = -1.106e-3  # K−1
    # Planck constant
    sigma = 5.670374419e-8  # W⋅m−2⋅K−4

    # flux equivalent brightness temperature
    Tf = (abs(olr) / sigma) ** (1.0 / 4) # (Stefan boltzman orl = sigma T^4 (changed to T =..) 

    # this is a empirical quadratic relation
    tb = (((aa**2 + 4 * bb * Tf) ** (1.0 / 2)) - aa) / (2 * bb)
    return tb

def add_tb_11(dataset):
    """Add brightness temperature 'tb_11' (K) computed from 'rlut'."""
    dataset["tb_11"] = get_tb(dataset["rlut"])
    
    dataset['tb_11'].attrs['units'] = 'K'
    
    dataset['tb_11'].attrs['long_name'] = 'estimated Tb at 11micronmeter'
    dataset['tb_11'].attrs['short_name'] = 'Tb'

    return dataset 

# add variables
def add_input_vars(dataset): 
    """Add rain rate (mm h-1), IWP and Tb to the dataset."""
    dataset = add_precip_tot_rate(dataset)
    dataset = add_iwp(dataset)
    dataset = add_tb_11(dataset)
    dataset = add_precip_tot_rate(dataset)
    return dataset


############################################
############ resample to lon lat #######
###################################

def get_nn_lon_lat_index(nside, lons, lats):
    '''
    uses healpy ang2pix function to create index for which cell belongs in each gridcell
    from https://easy.gems.dkrz.de/Processing/healpix/lonlat_remap.html
    '''
    import numpy as np
    import xarray as xr
    import healpy

    
    lons2, lats2 = np.meshgrid(lons, lats)
    return xr.DataArray(
        healpy.ang2pix(nside, lons2, lats2, nest=True, lonlat=True),
        coords=[("latitude", lats), ("longitude", lons)],
    )

    
def resample_to_lon_lat(dataset, variable,zoom = 8, to_imerg = True, lats = None, lons = None, idx = None): 
    ''' 
    resamples a variable of a given dataset to  lon lat
     => For each regular grid point, find the closest ICON model cell and grab its value
    get_nn_lon_lat_index(nside, lons, lats) 
    nside = based on zoom,
    lons, lats = from Imerg grid OR set manually e.g. linspace(lon_min,lon_max,ncount)
    output: dataarray, resampled 
    '''
    import numpy as np
    import xarray as xr
    import healpy

    if idx is None:  # only need lons/lats if computing idx
        if to_imerg:
            imerg_grid = xr.open_dataset("../output/aux/imerg_grid.nc", engine="h5netcdf")
            lons = imerg_grid.longitude.values
            lats = imerg_grid.latitude.values
        else:
            if lats is None or lons is None:
                raise ValueError("Must provide lats and lons when to_imerg=False")
        idx = get_nn_lon_lat_index(2**zoom, lons, lats)
        
    
    lon_lat = dataset[variable].isel(time=0, cell=idx)
    # rename to longitue/latitude
    lon_lat = add_unit(lon_lat)
    return lon_lat

def add_unit(dataarray):
    '''
    renames coords to longitude/latitude 
    adds degrees as unit
    '''
    #dataarray = dataarray.rename({'lat': 'latitude', 'lon': 'longitude'})
    dataarray['latitude'].attrs['units'] = 'degrees_north'
    dataarray['longitude'].attrs['units'] = 'degrees_east'
    return dataarray
    
##############################################
########## select one timestamp of icon data ##
#################################################
def select_time(dataset, date): 
    """Select a single timestamp (keeps the time dimension)."""
    ds = dataset.sel(time = slice(date, date))
    return ds

def select_vars(dataset,vlist=["pr", "rlut", "tas", "qsvi","clivi","qgvi","crs"]):
    """Subset the dataset to the variables in `vlist`."""
    ds = dataset[vlist] 
    return ds
##############################################
########## create 3hly timestamps e.g. for importing more than one##
#################################################

def create_3h_timestamps(start,end):
    """List of 3-hourly timestamp strings ('YYYY-MM-DD-HHMM') from start to end."""
    import pandas as pd 
    dates = pd.date_range(start = start,end = end, freq="3h").strftime("%Y-%m-%d-%H%M").tolist()
    return dates


############################
#### for comparison Flux equivalent
####################
def get_tf(olr):
    """
    from https://tobac.readthedocs.io/en/latest/examples/Example_ICON_MCS_tracking/Example_ICON_MCS_tracking.html
    
    This function converts outgoing longwave radiation to flux equivalent brightness temperatures Tf based on slingo 2001

    Args:
        olr(xr.DataArray or numpy array): 2D field of model output with OLR

    Returns:
        tb(xr.DataArray or numpy array): 2D field with estimated brightness temperatures
    """
    # constants
    aa = 1.228
    bb = -1.106e-3  # K−1
    # Planck constant
    sigma = 5.670374419e-8  # W⋅m−2⋅K−4

    # flux equivalent brightness temperature
    Tf = (abs(olr) / sigma) ** (1.0 / 4) # (Stefan boltzman orl = sigma T^4 (changed to T =..) 

    return Tf
def add_tf(dataset):
    dataset["tf"] = get_tf(dataset["rlut"])
    
    dataset['tf'].attrs['units'] = 'K'
    
    dataset['tf'].attrs['long_name'] = 'flux equivalent Brightness tempoerature'
    dataset['tf'].attrs['short_name'] = 'Tf'

    return dataset 

#######################
#### open dateslist of icon images##
# kinda hard coded with zoom level etc ####
####################
def open_icon_images(dateslist):
    """For each timestamp, load ICON (zoom 9) rain rate, Tb and IWP on the IMERG grid.
    Returns three DataArrays (precip, tb, iwp) concatenated along time."""
    import xarray as xr 
    icon_precip = []
    icon_tb = []
    icon_iwp = []
    
    zoom = 9
    dataset_total = open_ngc4008(zoom=zoom)
        
    for date in dateslist:  # fix: was using global `dates` instead of argument
        vlist = ["pr", "crs", "rlut", "clivi", "qsvi", "qgvi"]
        
        dataset = select_time(dataset_total, date)
        dataset = select_vars(dataset, vlist)
        
        dataset = add_precip_tot_rate(dataset)
        dataset = add_tb_11(dataset)
        dataset = add_iwp(dataset)  # check your actual function name
        
        precip = resample_to_lon_lat(dataset, "rain_tot_rate", to_imerg=True)
        tb    = resample_to_lon_lat(dataset, "tb_11",          to_imerg=True)
        iwp   = resample_to_lon_lat(dataset, "iwp",            to_imerg=True)
        
        icon_precip.append(precip)
        icon_tb.append(tb)
        icon_iwp.append(iwp)
    
    precip_icon = xr.concat(icon_precip, dim="time").compute()
    tb_icon     = xr.concat(icon_tb,     dim="time").compute()
    iwp_icon    = xr.concat(icon_iwp,    dim="time").compute()
    
    return precip_icon, tb_icon, iwp_icon
    
def open_rlut_icon(dateslist):
    """For each timestamp, load ICON (zoom 9) OLR and Tf on the IMERG grid.
    Returns two DataArrays (rlut, tf) concatenated along time."""
    import xarray as xr 
    icon_rlut = []
    icon_tf = []

    zoom = 9
    dataset_total = open_ngc4008(zoom=zoom)
        
    for date in dateslist:  
        vlist = ["crs", "rlut"]
        
        dataset = select_time(dataset_total, date)
        dataset = select_vars(dataset, vlist)
        
      
        dataset = add_tf(dataset)
        
         
        rlut = resample_to_lon_lat(dataset, "rlut", to_imerg=True)
        tf = resample_to_lon_lat(dataset, "tf", to_imerg=True)
        

        icon_rlut.append(rlut)
        icon_tf.append(tf)


    
    icon_rlut = xr.concat(icon_rlut, dim="time").compute()
    icon_tf = xr.concat(icon_tf, dim="time").compute()

    return icon_rlut, icon_tf