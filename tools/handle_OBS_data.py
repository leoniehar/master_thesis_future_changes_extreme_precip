from http.client import RemoteDisconnected
##############################################
###### Import NASA Tb as xr ds ##################
##############################################

def load_nasatb_as_ds(date, second_image = False, both_images = False): 
    '''
    Open NASA Global Merged IR V1 Tb (GPM_MERGIR) from GES DISC for `date` ("YYYY-MM-DD-HHMM").
    Needs Earthdata credentials.
    Default: first image of the granule; second_image=True: second image (+30 min);
    both_images=True: both (second_image wins if both are set).
    Returns None if no granule is found or the second image is missing.
    
    - NASA Global Merged IR V1 brightness temperature product (NASA-Tb)
    - Janowiak et al. 2001
    - INFO GPM: https://gpm.nasa.gov/data/directory/ncepcpc-level-3-merged-infrared-brightness-temperatures-0
    - GES DISC doc: https://disc.gsfc.nasa.gov/datasets/GPM_MERGIR_1/summary
    - https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-mergir-1
    '''
    import earthaccess
    import xarray as xr
    from datetime import datetime
    import time
    from http.client import RemoteDisconnected


    # Convert date to format for Earthdata
    dt = datetime.strptime(date, "%Y-%m-%d-%H%M")
    start_time = dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_time = start_time  # single timestamp
    
    # This will work if Earthdata prerequisite files have already been generated
    auth = earthaccess.login()
    
    # Search for granules
    results = earthaccess.search_data(
        short_name = "GPM_MERGIR",
        temporal=(start_time, end_time),
        bounding_box=(-180, -30, 180, 30) # appears to have no effect (but was included in example so kept)
    )
    #print(results)
    if len(results) == 0:
        print(f"No Nasa data found for {date} - skipping")
        return None
    
    for attempt in range(5):
        try:
            fs = earthaccess.open(results)
            ds = xr.open_mfdataset(fs, engine="h5netcdf")
            break  
        except (RemoteDisconnected, ConnectionError, OSError) as e:
            if attempt < 4:  # don't sleep after the last attempt
                print(f"Attempt {attempt + 1}/5 failed: {e} — retrying in 30s...")
                time.sleep(30)
            else:
                print(f"All 5 attempts failed for {date}")
                raise  # re-raise the original exception instead of silently continuing

    if second_image is True:
        if ds.sizes["time"] < 2:
            print(f"NASA-Tb second image requested but only {ds.sizes['time']} image(s) found for {date} - skipping")
            return None
        ds = ds.isel(time=slice(1, 2))
    elif both_images is True: 
        ds = ds
    else:
        ds = ds.isel(time=slice(0, 1))


    return ds 
    
##############################################
###### Import IMERG as xr ds ##################
##############################################
def load_imerg_as_ds(date): 
    '''
    Open IMERG V07 half-hourly precipitation (GPM_3IMERGHH, 0.1°), group "Grid", for `date`
    ("YYYY-MM-DD-HHMM"), sorted by time. Needs Earthdata credentials.
    Returns None if no granule is found.
    
    - NCEP/CPC L3 Half Hourly 4km Global (60S - 60N) Merged IR
    - Huffman, G.J., E.F. Stocker, D.T. Bolvin, E.J. Nelkin, Jackson Tan (2023), GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07, Greenbelt, MD, Goddard Earth Sciences Data and Information Services Center (GES DISC), Accessed: [Data Access Date], 10.5067/GPM/IMERG/3B-HH/07           
    - https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary?keywords=%22IMERG%20final%22
    '''
    import earthaccess
    import xarray as xr
    from datetime import datetime

    
    # Convert date to format for Earthdata
    dt = datetime.strptime(date, "%Y-%m-%d-%H%M")
    start_time = dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_time = start_time  # single timestamp
    
    # This will work if Earthdata prerequisite files have already been generated
    auth = earthaccess.login()
    
    # Search for granules
    results = earthaccess.search_data(
        #short_name="GPM_3IMERGM",
        short_name = "GPM_3IMERGHH",
        version="07",
        temporal=(start_time,end_time),
        bounding_box=(-180, -30, 180, 30)
    )
    
    if len(results) == 0:
        print(f"No IMERG data found for {date} - skipping")
        return None
        
    else:   
        for attempt in range(5):
            try:
                fs = earthaccess.open(results) # Extracts URLs from the results variable
                
                ds = xr.open_mfdataset(
                    fs,
                    engine="h5netcdf",
                    group="Grid",
                    combine="nested",
                    concat_dim="time")
                
                break  
            except (RemoteDisconnected, ConnectionError, OSError) as e:
                if attempt < 4:  # don't sleep after the last attempt
                    print(f"Attempt {attempt + 1}/5 failed: {e} — retrying in 30s...")
                    time.sleep(30)
                else:
                    print(f"All 5 attempts failed for {date}")
                    raise  # re-raise the original exception instead of silently continuing
        
        # fs = earthaccess.open(results) # Extracts URLs from the results variable
        
        # ds = xr.open_mfdataset(
        #     fs,
        #     engine="h5netcdf",
        #     group="Grid",
        #     combine="nested",
        #     concat_dim="time")
   
                
    
        ds = ds.sortby("time")

    return ds 

##############################################
###### Import CCIC as xr ds ##################
##############################################
def load_ccic_as_ds(date, second_image = False,both_images = False): 
    '''
    Open CCIC CPCIR record (AWS zarr) for `date` ("YYYY-MM-DD-HHMM").
    Image selection like load_nasatb_as_ds (first / second_image / both_images).
    Returns None if the file is not found or the second image is missing.
    
    - AWS: https://registry.opendata.aws/ccic/
    - documentation: https://ccic.readthedocs.io/en/latest/dataset_and_file_structure.html
    - cite: Amell, A., Pfreundschuh, S., and Eriksson, P.: The Chalmers Cloud Ice Climatology: Retrieval implementation and validation, EGUsphere [preprint], https://doi.org/10.5194/egusphere-2023-1953         
    '''
    import ccic
    import xarray as xr
    from datetime import datetime

    # date to datetime
    dt = datetime.strptime(date, "%Y-%m-%d-%H%M")
    # and tfrom datetime to reuired format
    date_str = dt.strftime("%Y%m%d%H%M")

    year = dt.strftime("%Y")
    #date = "200606061800" # YYYYMMDDHHMM

    try: 
    
        ds = xr.open_zarr(
            f's3://chalmerscloudiceclimatology/record/cpcir/{year}/ccic_cpcir_{date_str}.zarr',
            storage_options={"anon": True},
            consolidated=True
        )
        if second_image is True:
            if ds.sizes["time"] < 2:
                print(f"CCIC second image requested but only {ds.sizes['time']} image(s) found for {date} - skipping")
                return None
            ds = ds.isel(time=slice(1, 2))
        elif both_images is True:
            ds = ds 
        else:
            ds = ds.isel(time=slice(0, 1))
    
    except Exception as e:
        print(f"No CCIC data found for {date} - skipping ({e})")
        return None
    # dataset
    return ds

##############################################
###### allign coords logic of ccic and imerg with tb ##################
##############################################
def allign_imerg_coords_logic_with_tb(data):
    '''
    Aligns the coords logic of IMERG with tb (time,lat,lon)
    drops dims
    set datetime
    '''
    imerg_clean = data.drop_dims(["nv", "lonv", "latv"])
    # format 
    imerg_clean = imerg_clean.transpose("time", "lat", "lon")
    imerg_clean["time"] = imerg_clean.indexes["time"].to_datetimeindex(time_unit = "ns")
    
    return imerg_clean

def allign_ccic_coords_logic_with_tb(data):
    '''
    Alligns the coords logic of CCIC with tb (time,lat,lon)
    drops dims
    set datetime
    change lat to ascending
    '''
    ccic_clean = data.rename({"latitude": "lat","longitude": "lon"})
    
    ccic_clean = ccic_clean.drop_dims(["ci_bounds"])
    ccic_clean = ccic_clean.transpose("time", "lat", "lon")
    
    if ccic_clean.lat[0] > ccic_clean.lat[-1]:
        ccic_clean = ccic_clean.sortby('lat')

    
    return ccic_clean

def crop_tropical_belt_buffer(data, lat_bound):
    '''
    lat_bound = at which boundary to crop, expects ascending lat
    '''
    upper= lat_bound
    lower = -lat_bound
    ds_tropics = data.sel(lat=slice(lower, upper))
    return ds_tropics


##############################################
###### combined functions to loadd and clean ###
######## SELECT 1 variable ##################
##############################################
def load_clean_crop_tb(date, buffer):
    """
    NASA-Tb at `date` (first image), cropped to |lat| <= buffer. 2D DataArray "Tb" (K), or None.
    """ 
    tb = load_nasatb_as_ds(date)
    if tb is None:
        return None
    tb_cropped = crop_tropical_belt_buffer(tb,buffer)
    tb_cropped = tb_cropped["Tb"]
    
    tb_cropped = tb_cropped.rename({'lat': 'latitude', 'lon': 'longitude'})
    
    tb_cropped.attrs['units'] = 'K'
    tb_cropped.attrs['long_name'] = "Nasa-Tb"
    tb_cropped.attrs['short_name'] = "Tb"

    tb_cropped = tb_cropped.isel(time = 0)
    
    print(f"Tb data loaded for {date}, cropped, 'Tb' selected, longitude/latitude rename, assigned attrs,drop timedim")
    return tb_cropped
    
def load_clean_crop_imerg(date, buffer):
    """
    IMERG precipitation (mm h-1) at `date`, cropped to |lat| <= buffer, fill values masked. 2D DataArray or None.
    """
    imerg = load_imerg_as_ds(date)
    if imerg is None:
        return None
    imerg_clean = allign_imerg_coords_logic_with_tb(imerg)
    imerg_cropped = crop_tropical_belt_buffer(imerg_clean,buffer)
    precip = imerg_cropped["precipitation"]
    precip = precip.where(precip > -9999)  # mask fill values

    precip = precip.rename({'lat': 'latitude', 'lon': 'longitude'})
    
    precip.attrs['units'] = 'mm h-1'
    precip.attrs['long_name'] = "IMERG Precipitation"
    precip.attrs['short_name'] = "Precipitation"
    
    precip = precip.isel(time = 0)
    
    print(f"IMERG data loaded for {date}, cleaned, cropped, 'precipitation' selected, longitude/latitude rename, assigned attrs,drop timedim")
    return precip
    
def load_clean_crop_ccic(date, buffer):
    """
    CCIC total ice water path "tiwp" (kg m-2) at `date` (first image), cropped to |lat| <= buffer. 2D DataArray or None.
    """
    ccic = load_ccic_as_ds(date)
    if ccic is None:
        return None
    ccic_clean = allign_ccic_coords_logic_with_tb(ccic)
    ccic_cropped = crop_tropical_belt_buffer(ccic_clean,buffer)
    tiwp = ccic_cropped["tiwp"]

    tiwp = tiwp.rename({'lat': 'latitude', 'lon': 'longitude'})
    
    tiwp.attrs['units'] = 'kg m-2'#'kg m$^{-2}$'
    tiwp.attrs['long_name'] = "CCIC - IWP"
    tiwp.attrs['short_name'] = "IWP"
    
    tiwp = tiwp.isel(time = 0)
    
    print(f"CCIC data loaded for {date}, cleaned, cropped, 'tiwp' selected, longitude/latitude rename, assigned attrs, drop timedim")
    return tiwp

##############################################
###### combined functions to loadd and clean ###
######## SELECT 1 variable ##################
### SELECTED SECOND IMAGE OF THE TIMESTAMP ####
##############################################

##############################################
def load_clean_crop_tb_secondimage(date, buffer):
    """Like load_clean_crop_tb / _ccic, but the second image of the granule (date + 30 min)."""

    tb = load_nasatb_as_ds(date, second_image = True)
    if tb is None:
        return None
    tb_cropped = crop_tropical_belt_buffer(tb,buffer)
    tb_cropped = tb_cropped["Tb"]
    
    tb_cropped = tb_cropped.rename({'lat': 'latitude', 'lon': 'longitude'})
    
    tb_cropped.attrs['units'] = 'K'
    tb_cropped.attrs['long_name'] = "Nasa-Tb"
    tb_cropped.attrs['short_name'] = "Tb"

    tb_cropped = tb_cropped.isel(time = 0)
    
    print(f"Tb data loaded for {date}+30min, cropped, 'Tb' selected, longitude/latitude rename, assigned attrs,drop timedim")
    return tb_cropped
    
    
def load_clean_crop_ccic_secondimage(date, buffer):
    """Like load_clean_crop_tb / _ccic, but the second image of the granule (date + 30 min)."""

    ccic = load_ccic_as_ds(date, second_image = True)
    if ccic is None:
        return None
    ccic_clean = allign_ccic_coords_logic_with_tb(ccic)
    ccic_cropped = crop_tropical_belt_buffer(ccic_clean,buffer)
    tiwp = ccic_cropped["tiwp"]

    tiwp = tiwp.rename({'lat': 'latitude', 'lon': 'longitude'})
    
    tiwp.attrs['units'] = 'kg m-2'#'kg m$^{-2}$'
    tiwp.attrs['long_name'] = "CCIC - IWP"
    tiwp.attrs['short_name'] = "IWP"
    
    tiwp = tiwp.isel(time = 0)
    
    print(f"CCIC data loaded for {date}+30min, cleaned, cropped, 'tiwp' selected, longitude/latitude rename, assigned attrs, drop timedim")
    return tiwp


def load_clean_crop_tb_both_images(date, buffer):
    """
    Like load_clean_crop_tb / _ccic, but one fetch for both images:
    returns (image at date, image at date + 30 min). Second is None if only one image exists; (None, None) if no data.
    """

    tb = load_nasatb_as_ds(date,both_images = True)  # single network call
    if tb is None:
        return None, None
    
    # Slice both images before any processing
    img0 = tb.isel(time=slice(0, 1))
    img1 = tb.isel(time=slice(1, 2)) if tb.sizes["time"] >= 2 else None

    def _process(ds):
        ds = crop_tropical_belt_buffer(ds, buffer)["Tb"]
        ds = ds.rename({'lat': 'latitude', 'lon': 'longitude'})
        ds.attrs.update({'units': 'K', 'long_name': 'Nasa-Tb', 'short_name': 'Tb'})
        return ds.isel(time=0)
    print(f"Tb data loaded for {date}, if applicable both images returned, cropped, 'Tb' selected, longitude/latitude rename, assigned attrs,drop timedim")

    return _process(img0), (_process(img1) if img1 is not None else None)


def load_clean_crop_ccic_both_images(date, buffer):
    """
    Like load_clean_crop_tb / _ccic, but one fetch for both images:
    returns (image at date, image at date + 30 min). Second is None if only one image exists; (None, None) if no data.
    """

    ccic = load_ccic_as_ds(date, both_images = True)  # single network call
    if ccic is None:
        return None, None

    img0 = ccic.isel(time=slice(0, 1))
    img1 = ccic.isel(time=slice(1, 2)) if ccic.sizes["time"] >= 2 else None

    def _process(ds):
        ds = allign_ccic_coords_logic_with_tb(ds)
        ds = crop_tropical_belt_buffer(ds, buffer)["tiwp"]
        ds = ds.rename({'lat': 'latitude', 'lon': 'longitude'})
        ds.attrs.update({'units': 'kg m-2', 'long_name': 'CCIC - IWP', 'short_name': 'IWP'})
        return ds.isel(time=0)

    print(f"CCIC data loaded for {date}, if applicable both images returned, cleaned, cropped, 'tiwp' selected, longitude/latitude rename, assigned attrs, drop timedim")
    return _process(img0), (_process(img1) if img1 is not None else None)

#################################################
###### things for 3 hourly mean images######
###########################################

def create_timestamps_of_3hours(date): 
    '''
    creates array with 6 timestamps based on an input timestamp => 6 timestamps from previous 30min steps)
    '''
    from datetime import datetime, timedelta
    
    timestamps = []
    dt = datetime.strptime(date, "%Y-%m-%d-%H%M")
    
    for i in range(6):  # 3 hours = 6 steps of 30 min
        timestamps.append((dt - timedelta(minutes=30*i)).strftime("%Y-%m-%d-%H%M"))
    # example  ["2006-06-06-1800", "2006-06-06-1730", "2006-06-06-1700", "2006-06-06-1630", "2006-06-06-1600", "2006-06-06-1530"]
    return timestamps
    
def create_timestamps_of_3hours_hourly(date): 
    """List of 4 timestamps in 60-min steps back from `date` (date, -1 h, -2 h, -3 h)."""

    from datetime import datetime, timedelta
    
    timestamps = []
    dt = datetime.strptime(date, "%Y-%m-%d-%H%M")
    
    for i in range(4):  
        timestamps.append((dt - timedelta(minutes=60*i)).strftime("%Y-%m-%d-%H%M"))

    return timestamps


def load_clean_crop_tb_forpast3hours(date, buffer):
    """
    Half-hourly images for the 3 h up to `date`: 6 images (date, date-30 min, ... date-150 min)
    from 4 hourly fetches; expects `date` on the full hour. Concatenated along time, sorted.
    """
    import xarray as xr
    stamps = create_timestamps_of_3hours_hourly(date)
    images = []

    for i, hour in enumerate(stamps):
        if i == 0:
            img0, _ = load_clean_crop_tb_both_images(hour, buffer)
            if img0 is not None: images.append(img0)

        elif i == len(stamps) - 1:
            _, img1 = load_clean_crop_tb_both_images(hour, buffer)
            if img1 is not None: images.append(img1)

        else:  # i in [1, 2] — ONE fetch, TWO images
            img0, img1 = load_clean_crop_tb_both_images(hour, buffer)
            if img0 is not None: images.append(img0)
            if img1 is not None: images.append(img1)

    ds = xr.concat(images, dim="time")
    return ds.sortby("time")


def load_clean_crop_imerg_forpast3hours(date,buffer):
    """Half-hourly IMERG for the 3 h up to `date` (6 images, missing ones skipped). Returns None if none could be loaded."""

    
    import xarray as xr 
    images = []
    stamps = create_timestamps_of_3hours(date)


    for _,hour in enumerate(stamps):
        full = load_clean_crop_imerg(hour, buffer)
        if full is None: 
            continue
        images.append(full)
    if len(images) == 0:
        return None
    ds = xr.concat(images, dim="time")
    ds = ds.sortby("time")
    return ds


def load_clean_crop_ccic_forpast3hours(date, buffer):
    """
    Half-hourly images for the 3 h up to `date`: 6 images (date, date-30 min, ... date-150 min)
    from 4 hourly fetches; expects `date` on the full hour. Concatenated along time, sorted.
    """
    import xarray as xr
    stamps = create_timestamps_of_3hours_hourly(date)
    images = []

    for i, hour in enumerate(stamps):
        if i == 0:
            img0, _ = load_clean_crop_ccic_both_images(hour, buffer)
            if img0 is not None: images.append(img0)

        elif i == len(stamps) - 1:
            _, img1 = load_clean_crop_ccic_both_images(hour, buffer)
            if img1 is not None: images.append(img1)

        else:
            img0, img1 = load_clean_crop_ccic_both_images(hour, buffer)
            if img0 is not None: images.append(img0)
            if img1 is not None: images.append(img1)

    ds = xr.concat(images, dim="time")
    return ds.sortby("time")

def get_3_hour_mean_pixelwise(data, min_images, ref_time):
    """Pixelwise time mean; pixels with fewer than `min_images` valid values become NaN. Result gets the scalar time `ref_time` ("YYYY-MM-DD-HHMM")."""

    import pandas as pd
    valid_count = data.count(dim="time")
    
    mean_image = data.where(valid_count >= min_images).mean(dim="time")
    ref_time_dt = pd.to_datetime(ref_time, format='%Y-%m-%d-%H%M')
    mean_image = mean_image.assign_coords(time=ref_time_dt)
    
    return mean_image
##### combi functions #####
## output is equivalent to load_clean_crop_ccic snapshot 
def load_calc_clean_mean_tb(date, buffer, min_images):
    """3 h mean Tb ending at `date`, cropped to |lat| <= buffer, `min_images` valid per pixel."""
    tb = load_clean_crop_tb_forpast3hours(date,buffer)
    tb_mean = get_3_hour_mean_pixelwise(tb, min_images= min_images,ref_time= date)
    return tb_mean

def load_calc_clean_mean_imerg(date, buffer, min_images):
    """3 h mean IMERG precipitation ending at `date`, cropped to |lat| <= buffer, `min_images` valid per pixel."""
    imerg = load_clean_crop_imerg_forpast3hours(date,buffer)
    imerg_mean = get_3_hour_mean_pixelwise(imerg, min_images= min_images,ref_time= date)
    return imerg_mean

def load_calc_clean_mean_ccic(date, buffer, min_images):
    """3 h mean CCIC IWP ending at `date`, cropped to |lat| <= buffer, `min_images` valid per pixel."""
    ccic = load_clean_crop_ccic_forpast3hours(date,buffer)
    ccic_mean = get_3_hour_mean_pixelwise(ccic, min_images= min_images,ref_time= date)
    return ccic_mean
##############################################
###### resample one dataarray to another SPATIALLY ########
##############################################
def resample_grids_old(data, ref_data):  # resample_grids_withoutgauss
    res = data.interp(
    latitude = ref_data.latitude,
    longitude = ref_data.longitude,
    method='nearest')
    return res

def resample_grids(data, ref_data, sigma = 2): # delet _with
    """
    Gaussian-smooth `data` (sigma in grid cells, spatial dims only; NaNs are first filled with the field mean
    and stay filled), then nearest-neighbour interpolate onto the grid of `ref_data`.
    """
    import numpy as np
    from scipy.ndimage import gaussian_filter

    
    # Replace NaN with mean of valid values
    data_filled = data.values.copy()
    # data_filled[np.isnan(data)] = np.nanmean(data)
    data_filled[np.isnan(data.values)] = np.nanmean(data.values)

    # make sure its only applied to spatial dims
    spatial_axes = (data.dims.index('latitude'), data.dims.index('longitude'))
    sigma_nd = [sigma if i in spatial_axes else 0 for i in range(data.ndim)]

    # gaussian filter
    data_values =  gaussian_filter(data_filled, sigma_nd)

    # assign to old datastructure so meta data is not lost 
    data_in = data.copy()
    data_in.data =data_values

    # normal resampling as before
    res = data_in.interp(
    latitude = ref_data.latitude,
    longitude = ref_data.longitude,
    method='nearest')
    return res


def apply_regrid(data, data_ref):
    """Regrid `data` to the grid of `data_ref` with xESMF (nearest_s2d). Keeps attrs, chunks lat/lon (<= 200). Expects dims lat/lon."""

    import xesmf as xe

    regridder = xe.Regridder(
        data,
        data_ref,
        method="nearest_s2d")

    out = regridder(data)

    out.attrs = {**data.attrs, **out.attrs}

    # chunks
    spatial_dims = [d for d in out.dims if d in ["lat", "lon"]]

    if spatial_dims:
        out = out.chunk({
            d: min(200, out.sizes[d])
            for d in spatial_dims
        })

    return out
##############################################
###### load multiple mean images #######
##############################################
def create_3h_timestamps(start,end):
    """List of 3-hourly timestamp strings ("YYYY-MM-DD-HHMM") from start to end."""

    import pandas as pd
    dates = pd.date_range(start = start,end = end, freq="3h").strftime("%Y-%m-%d-%H%M").tolist()
    return dates

def mean_precip_images_multiple_mean_images(dates):
    """3 h mean IMERG precipitation for each date (buffer=30, min_images=5 fixed), concatenated along time."""

    import xarray as xr
    obs_mean_images= []
    for date in dates:
        # load data
        precip = load_calc_clean_mean_imerg(date, buffer = 30, min_images= 5)
        obs_mean_images.append(precip)
    
    precip_obs = xr.concat(obs_mean_images, dim= "time")
    return precip_obs

def mean_tb_images_multiple_mean_images(dates, to_imerg= True, to_inputgrid= False, inputgrid = None):
    """
    3 h mean Tb for each date (buffer=32, min_images=5 fixed), concatenated along time.
    to_imerg: resample to the IMERG grid (../output/aux/imerg_grid.nc); to_inputgrid: resample to `inputgrid`
    (applied after the IMERG step if both are True).
    """
    import xarray as xr
    
    obs_mean_images= []

    if to_imerg is True: 
        # open grid 
        imerg_grid = xr.open_dataset("../output/aux/imerg_grid.nc").squeeze().drop_vars("time")
            
    for date in dates:
        # load data
        tb = load_calc_clean_mean_tb(date, buffer = 32, min_images= 5)

        if to_imerg is True: 
            tb =  resample_grids(tb,imerg_grid)
            print("resampled to imerg ref grid")
        if to_inputgrid is True: 
            tb =  resample_grids(tb,inputgrid)
            print("resampled to input grid")   

        obs_mean_images.append(tb)
    
            
    tb_obs = xr.concat(obs_mean_images, dim= "time")
    return tb_obs
    
def mean_iwp_images_multiple_mean_images(dates,to_imerg= True, to_inputgrid= False, inputgrid = None): 
    """
    3 h mean CCIC IWP for each date (buffer=32, min_images=5 fixed), concatenated along time.
    to_imerg: resample to the IMERG grid (../output/aux/imerg_grid.nc); to_inputgrid: resample to `inputgrid`
    (applied after the IMERG step if both are True).
    """
    import xarray as xr
    
    obs_mean_images= []
    if to_imerg is True: 
        # open grid 
        imerg_grid = xr.open_dataset("../output/aux/imerg_grid.nc").squeeze().drop_vars("time")
        
       
    for date in dates:
        # load data
        iwp = load_calc_clean_mean_ccic(date, buffer = 32, min_images= 5)

        if to_imerg is True: 
            iwp =  resample_grids(iwp,imerg_grid)
            print("resampled to imerg ref grid")
            
        if to_inputgrid is True: 
            iwp =  resample_grids(iwp,inputgrid)
            print("resampled to input grid")
        
        obs_mean_images.append(iwp)
    
    iwp_obs = xr.concat(obs_mean_images, dim= "time")
    
        
    return iwp_obs
