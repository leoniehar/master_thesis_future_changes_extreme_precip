##############################################
###### add bulk stats for anvils ###
##############################
def add_bulk_stats_anvil(features, segmentation_mask, tb_iris,precip_iris,iwp_iris):
    '''
    add bulk statsitics using tobac package
    for Tb, precip and iwp feld
    area
    '''
    from tobac.utils import get_statistics_from_mask
    import tobac
    import numpy as np
    import pandas as pd
    
    # Tb
    statistics = {}
    statistics['min_tb'] = np.min
    
    features_with_tb_stats = get_statistics_from_mask(features, segmentation_mask, tb_iris, statistic=statistics)
    
    # precip
    statistics = {}
    statistics['mean_precip'] = np.mean
    statistics['total_precip'] = np.sum
    statistics['max_precip'] = np.max
    
    
    features_with_precip_stats = get_statistics_from_mask(features, segmentation_mask, precip_iris, statistic=statistics)
    
    # iwp 
    statistics = {}
    statistics['mean_iwp'] = np.mean
    statistics['total_iwp'] = np.sum
    statistics['max_iwp'] = np.max
    
    features_with_iwp_stats = get_statistics_from_mask(features, segmentation_mask, iwp_iris, statistic=statistics)

    # add area
    area_tmp = tobac.calculate_area(features, segmentation_mask)

    # Drop existing area column if present (it's NaN anyway)
    features = features.drop(columns=['area'], errors='ignore')
    
    
    
    # merge to one ds
    df_merged = features.merge(
        features_with_iwp_stats[['feature', 'mean_iwp', 'total_iwp', 'max_iwp']],
        on='feature',
        how='left'
    )
    
    df_merged = df_merged.merge(
        features_with_precip_stats[['feature', 'mean_precip', 'total_precip', 'max_precip']],
        on='feature',
        how='left'
    )
    
    df_merged = df_merged.merge(
        features_with_tb_stats[['feature', 'min_tb']],
        on='feature',
        how='left'
    )
   
    df_merged = df_merged.merge(
        area_tmp[['feature', 'area']],
        on='feature',
        how='left'
    )

    # to prevent some saving error
    numeric_cols = ['mean_iwp', 'total_iwp', 'max_iwp', 'mean_precip', 'total_precip', 'max_precip', 'min_tb']
    for var in numeric_cols:
        df_merged[var] = df_merged[var].astype("float64")
    
    df_merged["time"] = pd.to_datetime(df_merged["time"].astype(str))
    
    return df_merged

def add_D_equ(data):
    '''
    calculates equivalent diameter based on given column
    D_eq =2*sqrt(ai/pi)
    =the diameter of an area-equal circle with area ai
    Input area in m², output in km.
    '''
    import numpy as np
    d_eq = 2*np.sqrt(data/np.pi)
    d_eq_km = d_eq/1000 # m => km
    return d_eq_km

##############################################
###### add bulk stats for precip cells ###
##############################

def add_bulk_stats_cell(features, segmentation_mask,precip_iris):
    '''
    add bulk statsitics using tobac package
    for precip and area
    '''
    from tobac.utils import get_statistics_from_mask
    import tobac
    import numpy as np
    import pandas as pd

    
    # precip
    statistics = {}
    statistics['mean_precip'] = np.mean
    statistics['total_precip'] = np.sum
    statistics['max_precip'] = np.max
    #statistics['percentiles'] = (np.percentile, {'q': [95,99]})
    
    
    features_with_precip_stats = get_statistics_from_mask(features, segmentation_mask, precip_iris, statistic=statistics)
    
    
    # add area
    area_tmp = tobac.calculate_area(features, segmentation_mask)


    # Drop existing area column if present (it's NaN anyway)
    features = features.drop(columns=['area'], errors='ignore')
   
    
  
    # merge to one ds    
    df_merged = features.merge(
        features_with_precip_stats[['feature', 'mean_precip', 'total_precip', 'max_precip']],
        on='feature',
        how='left'
    )
   
    df_merged = df_merged.merge(
        area_tmp[['feature', 'area']],
        on='feature',
        how='left'
    )

    # to prevent some saving error
    numeric_cols = ['mean_precip', 'total_precip', 'max_precip']
    for var in numeric_cols:
        df_merged[var] = df_merged[var].astype("float64")
    
    df_merged["time"] = pd.to_datetime(df_merged["time"].astype(str))
    
    return df_merged
##############################################
###### look up anvil Idx for precip features  ###
########################
def get_feature_of_segmask_for_feature_table(segmentation_mask, feature_table):
    ''' 
    for each feature in the feature table this functions looks up the cell index of the segmentation mask
    in my example: anvil feature (id) in segmenation mask for precip feature
    
    Input: 
        segmentation_mask = xr dataarray with latitude/ longitude coordinate
        feature_table = pandas dataframe (feature table from tobac)
    
    => output: list with length nrows feature_table with feature_anvil
    '''
    features_anvil =[]
    for index, row in feature_table.iterrows():
        # get lat lon data of the current row
        longitude_feature= row["longitude"]
        latitude_feature= row["latitude"]
           
        # select value of segmentation mask (aka anvil index) based on indexing lat lon coords
        # select nearest
        feature_anvil = int(segmentation_mask.sel(longitude=longitude_feature, latitude = latitude_feature, method = "nearest").values)
        features_anvil.append(feature_anvil)
    return features_anvil


def add_bulk_stats(features, segmentation_mask, layer, stats=["mean"]):
    """
    features:         segmentation feature table to add stats to
    segmentation_mask: mask for which stats are calculated
    layer:            iris cube to compute stats from
    stats:            list of statistics to compute, e.g. ["mean", "sum", "max", "min"]
    Returns the feature table with these columns.
    """
    from tobac.utils import get_statistics_from_mask
    import tobac
    import numpy as np

    layer_name = str(layer.name())  # iris cubes use .name()

    statistics = {}
    if "mean" in stats:
        statistics[f'mean_{layer_name}'] = np.mean
    if "sum" in stats:
        statistics[f'total_{layer_name}'] = np.sum
    if "max" in stats:
        statistics[f'max_{layer_name}'] = np.max
    if "min" in stats:
        statistics[f'min_{layer_name}'] = np.min

    features_with_stats = get_statistics_from_mask(
        features, segmentation_mask, layer, statistic=statistics
    )
    return features_with_stats