# bad timestamps
import pandas as pd
bad_timesteps = pd.to_datetime([
    '2023-06-16 12:00:00',
    '2023-06-05 21:00:00',
    '2023-06-13 21:00:00',
    '2023-12-05 18:00:00',
    '2023-12-07 06:00:00',
])

# included icon years
icon_years =  [str(y) for y in range(2021, 2050)] 

# subreions (plotting)
georegions = {"global": [-180,180,-30,30], 
           "africa_0":[-30, 30, -10, 30],
           "pacific":[-180, -120, -30, 30],
            "amazonas":[-80, -40, -10, 20],
             "maritime":[80, 160, -20, 30]}



################################
######################### VARIABLE SELECTION

# 
var_order_tracks_cellonly = [ 
'mean_precip_cell_mean','max_precip_cell_max', 'rain_volume_cell_mean',
    'd_eq_cell_mean',
 'min_dist_cell_km_mean',
'n_sister_cells_mean',
    'mean_iwp_cell_mean',
'lifetime_cell',
 'velo_cell_mean']


var_order_cell_features = [
    'mean_precip_cell',
     'max_precip_cell', 
    'rain_volume_cell',
    'd_eq_cell',
    'min_dist_cell_km',     
    'n_sister_cells',
    "mean_iwp_cell", ]
var_order_anvil_features=[
    'mean_precip_anvil',
    'rain_volume_anvil',
    'convective_rain_volume_anvil',
        'fraction_convection_rain_volume_anvil',
      'd_eq_anvil',
    "min_dist_anvil_km",
     'n_children_anvil',
       'min_tb_anvil',
    'mean_iwp_anvil',
    'max_iwp_anvil', 
    'iwp_volume_anvil']

var_order_domain = ['n_cells',  'cell_area_sum',  'rain_volume_cell_sum', 'n_anvils','anvil_area_sum','rain_volume_anvil_sum']


 

################################################
############################### colors

# colors
colorobs = "royalblue"
coloricon = "darkorange"

color_precip_icon = "dodgerblue"
color_precip_obs= "darkblue"

color_tb_icon = "orangered"
color_tb_obs = "firebrick"

color_iwp_icon = "violet"
color_iwp_obs  = "mediumorchid"

color_rlut_icon = "yellowgreen"
color_tf_icon = "darkorange"

color_structure_icon = "red"
color_structure_obs = "darkred"

color_n_icon = "yellowgreen"
color_n_obs = "green"

color_dist_icon= "olivedrab"
color_dist_obs = "darkolivegreen"

color_velo_icon = "darkorange"
color_velo_obs = "sienna"

color_lifetime_icon = "coral"
color_lifetime_obs  = "brown"

color_pe_icon = "mediumpurple"
color_pe_obs = "indigo"




# color mapping function
def get_var_color(var, source="ICON"):
    src = source.upper()
    color_map = {
        "precip":   {"ICON": color_precip_icon, "OBS": color_precip_obs},
        "rain":     {"ICON": color_precip_icon, "OBS": color_precip_obs},
        "tb":       {"ICON": color_tb_icon,  "OBS": color_tb_obs},
        "bt":       {"ICON": color_tb_icon,  "OBS": color_tb_obs},
        "iwp":      {"ICON": color_iwp_icon,     "OBS": color_iwp_obs},
        "area":     {"ICON": color_structure_icon, "OBS": color_structure_obs},
        "d_eq":     {"ICON": color_structure_icon, "OBS": color_structure_obs},
        "dist":     {"ICON": color_dist_icon, "OBS": color_dist_obs},
        "n_sister": {"ICON": color_n_icon, "OBS": color_n_obs},
        "n_children": {"ICON": color_n_icon, "OBS": color_n_obs},
        "velo": {"ICON": color_velo_icon, "OBS": color_velo_obs},
        "pe": {"ICON": color_pe_icon, "OBS": color_pe_obs},
         "lifetime":   {"ICON": color_lifetime_icon, "OBS": color_lifetime_obs},
          "n_cells":   {"ICON": coloricon, "OBS": colorobs},
          "n_anvils":   {"ICON": coloricon, "OBS": colorobs},
        
    }
    for key, shades in color_map.items():
        if key in var.lower():
            return shades.get(src, "grey")
    return "grey"
#########################
## units


var_unit_map = {
    "fraction_convection":      {"unit": "-",               "factor": 1},
    "convective_rain_volume":   {"unit": "m$^2$ mm hr$^{-1}$",  "factor": 1}, #= m2 *kg/m2 h = kg/h
    "rain_volume":              {"unit": "m$^2$ mm hr$^{-1}$",  "factor": 1},
    "precip":                   {"unit": "mm hr$^{-1}$",  "factor": 1},
    "rain":                     {"unit": "mm hr$^{-1}$",    "factor": 1},
    "min_tb":                   {"unit": "K",               "factor": 1},
    "tb":                       {"unit": "K",               "factor": 1},
    "bt":                       {"unit": "K",               "factor": 1},
    "iwp_volume":                {"unit": "kg",     "factor": 1}, #m$^{-2}$
    "iwp":                       {"unit": "kg m$^{-2}$",     "factor": 1},
    "area":                      {"unit": "km$^2$",          "factor": 1},
    "d_eq":                      {"unit": "km",              "factor": 1},
    "min_dist":                  {"unit": "km",              "factor": 1},
    "dist":                      {"unit": "km",              "factor": 1},
    "n_sister":                  {"unit": "counts",           "factor": 1},
    "n_children":                {"unit": "counts",           "factor": 1},
    "velo":                      {"unit": "m s$^{-1}$",      "factor": 1},
    "pe_":                       {"unit": "%",               "factor": 1},
    "lifetime":                  {"unit": "hours",           "factor": 1},
    "n_cells":                   {"unit": "counts",           "factor": 1},
    "n_anvils":                  {"unit": "counts",           "factor": 1},}

 
def get_var_unit(var, source="ICON"):
    '''
    Returns (unit, factor) for a variable name based on substring matching,
    same pattern as get_var_color. Supports optional per-source overrides
    if "unit" or "factor" is itself a dict, e.g.
        {"unit": "mm", "factor": {"ICON": 1000, "OBS": 1}}
    '''
    src = source.upper()
    v = var.lower()
    for key, meta in var_unit_map.items():
        if key in v:
            unit = meta["unit"]
            factor = meta["factor"]
            if isinstance(unit, dict):
                unit = unit.get(src, "tba")
            if isinstance(factor, dict):
                factor = factor.get(src, 1)
            return unit, factor
    return "tba", 1
    
#############################################
#### labels

var_label_map = {
    # --- lifetime-integrated cell properties (var_order_tracks_cellonly) ---
    'mean_precip_cell_mean':  r'$\bar{R}_{\mathrm{mean,cell}}$',
    'max_precip_cell_max':    r'$R_{\mathrm{max,cell}}^{\max}$',
    'rain_volume_cell_mean':  r'$\bar{V}_{\mathrm{rain,cell}}$',   # NB: see note below
    'rain_volume_cell_sum':   r'$V_{\mathrm{rain,cell}}^{\Sigma}$',
    'd_eq_cell_mean':         r'$\bar{D}_{\mathrm{eq,cell}}$',
    'min_dist_cell_km_mean':  r'$\overline{NNdist}_{\mathrm{cell}}$',
    'n_sister_cells_mean':    r'$\bar{N}_{\mathrm{sister}}$',
    'lifetime_cell':          r'$lifetime_{\mathrm{cell}}$',
    'velo_cell_mean':         r'$\bar{u}_{\mathrm{cell}}$',
    'mean_iwp_cell_mean':         r'$\overline{IWP}_{\mathrm{mean,cell}}$',
    

    

    # --- cell features (var_order_cell_features) ---
    'mean_precip_cell':       r'$R_{\mathrm{mean,cell}}$',
    'max_precip_cell':        r'$R_{\mathrm{max,cell}}$',
    'rain_volume_cell':       r'$V_{\mathrm{rain,cell}}$',
    'd_eq_cell':              r'$D_{\mathrm{eq,cell}}$',
    'min_dist_cell_km':       r'$NNdist_{\mathrm{cell}}$',
    'n_sister_cells':         r'$N_{\mathrm{sister}}$',


    'PE_anvil': r'$PE_{\mathrm{anvil}}$',
    'PE_cell': r'$PE_{\mathrm{cell}}$',
    

    # --- anvil features (var_order_anvil_features) ---
    'mean_precip_anvil':                    r'$R_{\mathrm{mean,anvil}}$',
    'rain_volume_anvil':                    r'$V_{\mathrm{rain,anvil}}$',
    'convective_rain_volume_anvil':         r'$V_{\mathrm{conv,anvil}}$',
    'fraction_convection_rain_volume_anvil': r'$f_{\mathrm{conv,anvil}}$',
    'mean_iwp_anvil':                       r'$IWP_{\mathrm{mean,anvil}}$',
    'max_iwp_anvil':                        r'$IWP_{\mathrm{max,anvil}}$',
    'iwp_volume_anvil':                     r'$V_{\mathrm{IWP,anvil}}$',
    'min_tb_anvil':                         r'$BT_{\mathrm{min,anvil}}$',
    'd_eq_anvil':                           r'$D_{\mathrm{eq,anvil}}$',
    'min_dist_anvil_km':                    r'$NNdist_{\mathrm{anvil}}$',
    'n_children_anvil':                     r'$N_{\mathrm{cores}}$',

    # --- domain wide (var_order_domain) ---
    'n_cells':                r'$N_{\mathrm{tot,cell}}$',
    'cell_area_sum':          r'$A_{\mathrm{tot,cell}}$',
    'rain_volume_cell_sum': r'$V_{\mathrm{tot,cell}}$',  # see naming clash note below
    'n_anvils':               r'$N_{\mathrm{tot,anvil}}$',
    'anvil_area_sum':         r'$A_{\mathrm{tot,anvil}}$',
    'rain_volume_anvil_sum':  r'$V_{\mathrm{tot,anvil}}$',
}
#############################################
#### labels
var_label_long_map = {
    'mean_precip_cell_mean':  'mean rain rate cell',
    'max_precip_cell_max':    'max rain rate cell',
    'rain_volume_cell_mean':  'rain volume cell (mean)',
    'rain_volume_cell_sum':   'rain volume cell (sum)',
    'd_eq_cell_mean':         'mean equiv. diameter cell',
    'min_dist_cell_km_mean':  'mean min. distance to next cell',
    'n_sister_cells_mean':    'mean number of sister cells',
    'lifetime_cell':          'cell lifetime',
    'velo_cell_mean':         'mean cell velocity',
    'mean_iwp_cell_mean':      'mean IWP cell',

    'mean_precip_cell':       'mean rain rate cell feature',
    'max_precip_cell':        'max rain rate cell feature',
    'rain_volume_cell':       'rain volume cell feature',
    'd_eq_cell':              'equiv. diameter cell feature',
    'min_dist_cell_km':       'min. distance to next cell feature',
    'n_sister_cells':         'number of sister cell features',

    'PE_anvil': r'PE anvil',
    'PE_cell': r'PE cell',
    

    'mean_precip_anvil':                    'mean rain rate anvil',
    'rain_volume_anvil':                    'rain volume anvil',
    'convective_rain_volume_anvil':         'convective rain volume anvil',
    'fraction_convection_rain_volume_anvil': 'fraction of convective rain volume anvil',
    'mean_iwp_anvil':                       'mean IWP anvil',
    'max_iwp_anvil':                        'max IWP anvil',
    'iwp_volume_anvil':                     'IWP volume anvil',
    'min_tb_anvil':                         'minimum BT anvil',
    'd_eq_anvil':                           'equiv. diameter anvil',
    'min_dist_anvil_km':                    'min. distance to next anvil',
    'n_children_anvil':                     'number of cores',

    'n_cells':                'number of cells',
    'cell_area_sum':          'cell area sum',
    'rain_volume_cell_sum': 'rain volume cell sum',
    'n_anvils':               'number of anvils',
    'anvil_area_sum':         'anvil area sum',
    'rain_volume_anvil_sum':  'rain volume anvil sum',
}


#########################
### build var meta functions

def make_var_meta(var_names, source="ICON", get_hatch=None, base_hatches=None,
                   label_map=var_label_map, label_long_map=var_label_long_map,unit_overrides=None):
    '''
    unit_overrides: optional dict to hard-override unit/factor for specific
    variable names, bypassing substring matching entirely, e.g.
        unit_overrides = {"lifetime_cell": {"unit": "h", "factor": 1}}
    '''
    if get_hatch:
        if base_hatches is None:
            base_hatches = {"cell": "", "anvil": "xx"}
        def get_hatch(var):
            if "anvil" in var.lower():
                return base_hatches["anvil"]
            if "cell" in var.lower():
                return base_hatches["cell"]
            return ""
    else:
        def get_hatch(var):
            return ""

    label_map = label_map or {}
    label_long_map = label_long_map or {}
    unit_overrides = unit_overrides or {}

    meta = {}
    for var in var_names:
        if var in unit_overrides:
            unit = unit_overrides[var]["unit"]
            factor = unit_overrides[var]["factor"]
        else:
            unit, factor = get_var_unit(var, source)

        meta[var] = {
            "color": get_var_color(var, source),
            "hatch": get_hatch(var),
            "label": label_map.get(var, var),
            "label_long": label_long_map.get(var, var),
            "label_factor": var,
            "factor": factor,
            "unit": unit,
        }
    return meta
