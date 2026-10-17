# for binning
import numpy as np
import xarray as xr

def log_bins(low=-2, high=2, n=60):
    import numpy as np
    return np.logspace(low, high, n)

def linear_bins(*arrays, n=80, pad=1):
    import numpy as np
    lo = min(np.nanmin(a.values) for a in arrays)
    hi = max(np.nanmax(a.values) for a in arrays) 
    return np.linspace(lo - pad, hi + pad, n)

# maybe try? and check lol
def pendergrass_bins(low_mmhr=0.03/24, high_mmhr=300, pct=0.07):
    """
    Logarithmic bins with fixed percentage spacing (default 7% like Pendergrass)
    low_mmhr: dry threshold (0.03 mm/day converted to mm/hr)
    """
    edges = [low_mmhr]
    while edges[-1] < high_mmhr:
        edges.append(edges[-1] * (1 + pct))
    return np.array(edges)



def compute_pdf(
    data_list,
    bins,
    labels,
    filter_positive=False,
):
    """
    Compute per-timestep histograms for each dataset.
    All datasets must share the same time axis.
    Returns an xarray.Dataset ready to save as netCDF.
    """
    import numpy as np
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    
    data_vars = {}

    for data, label in zip(data_list, labels):
        hist_list = []
        for t in data.time:
            values = data.sel(time=t).values.flatten()
            values = values[~np.isnan(values)]
            if filter_positive:
                values = values[values > 0]
            counts, _ = np.histogram(values, bins=bins, density=False)
            hist_list.append(counts)

        time_coord = data.time.values

        safe = label.replace(" ", "_")
        data_vars[f"counts_{safe}"] = xr.DataArray(
            np.stack(hist_list, axis=0),          # (time, bin)
            dims=["time", "bin_center"],
            attrs={"label": label, "filter_positive": str(filter_positive)},
        )

    ds = xr.Dataset(
        data_vars,
        coords={
            "time":       time_coord,
            "bin_center": bin_centers,
            "bin_left":   ("bin_center", bins[:-1]),
            "bin_right":  ("bin_center", bins[1:]),
        },
        attrs={"filter_positive": str(filter_positive)},
    )
    return ds


def calc_area_weights(da):
    """cos(lat) weights normalised to sum 1, shape (latitude, longitude). Input: DataArray with dims latitude, longitude."""

    cos_lat = np.cos(np.deg2rad(da.latitude))  # (nlat,)
    weights_2d = cos_lat * xr.ones_like(da.longitude)  
    weights_2d = weights_2d / weights_2d.sum()  # a_grid / a_total
    return weights_2d
    

def compute_amount_distribution(
    data_list,
    bins,
    labels,
    filter_positive=False,
    area_weights=None,
):
    """
    Rain amount distribution (Pendergrass & Hartmann 2014, A1): per timestep, sum of weight*value per bin / ΔlnR.
    area_weights: DataArray from calc_area_weights (else equal weights). Bins must be positive.
    Returns Dataset with contri_<label>(time, bin_center).
    """

    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    delta_lnR = np.log(bins[1:]) - np.log(bins[:-1])
    
    data_vars = {}

    for data, label in zip(data_list, labels):
        AR_list = []

        if area_weights is not None:
            w = area_weights.values.flatten() # Agrid/ages (computed before) 

        for t in data.time:
            values = data.sel(time=t).values.flatten()
            weights = w.copy() if area_weights is not None else np.ones_like(values)
            
            valid = ~np.isnan(values)
            if filter_positive: # i dont do it
                valid &= (values > 0)
            
            values  = values[valid]
            weights = weights[valid]


            amount, _ = np.histogram(values, bins=bins, weights=weights * values) # sum gridpoints
            AR_list.append(amount / delta_lnR) # 1/ delta lnR

        time_coord = data.time.values

        safe = label.replace(" ", "_")
        data_vars[f"contri_{safe}"] = xr.DataArray(
            np.stack(AR_list, axis=0),
            dims=["time", "bin_center"],
            attrs={"label": label, "units": "mm h-1",
                   "description": "Pendergrass 2014 rain amount distribution"},
        )

    ds = xr.Dataset(
        data_vars,
        coords={
            "time":       time_coord,
            "bin_center": bin_centers,
            "bin_left":   ("bin_center", bins[:-1]),
            "bin_right":  ("bin_center", bins[1:]),
        },
    )
    return ds

    

def keep_only(ds, prefix):
    """Drop all data variables whose name does not start with `prefix`."""

    drop_vars = [v for v in ds.data_vars if not v.startswith(prefix)]
    return ds.drop_vars(drop_vars)
    

def get_cdf(ds):
    original_vars = list(ds.data_vars) 
    for var in original_vars:
        total = ds[var].sum(dim="bin_center")
        ds[f"cdf_{var}"] = ds[var].cumsum(dim="bin_center") / total
        ds[f"cdf_{var}"].attrs = {
            **ds[var].attrs,
            "description": "cumulative distribution function",
        }
    ds = keep_only(ds,"cdf")
    return ds


def plot_pdf_pair(
    ax,
    data_list,
    colors,
    labels,
    xlabel,
    ylabel ,
    alltimestamps = False, 
    main = True, 
    uncertainty = False,
    percentiles=(0.16,0.84),
    label_uncertainty = "±1σ",
    vlines=None, # lines ( x position, label, y height)
    xscale="linear", # x axis
    xlim=None,
    invert_x=False,
    yscale = "linear", # x axis
    cdf = False,
    ylim=None,
    title=None, # title
    legend = True,
):
    """
    Plot binned distributions as stairs on `ax`.
    data_list: DataArrays (time, bin_center) with coords bin_left/bin_right (e.g. from compute_pdf / get_cdf).
    Per entry: mean over time (main), every timestep (alltimestamps), percentile band of the daily means (uncertainty).
    cdf + invert_x plots 1 - cdf. vlines: list of (x, label, y), y in axes fraction.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr
    import seaborn as sns

    # plotting the different lines
    for data, color, label in zip(data_list, colors, labels):
        bins = np.append(data.bin_left.values, data.bin_right.values[-1]) # bin edges needed => take left edges and append the last right bin edge
        if alltimestamps:
            for t in data.time:
                if cdf == True and invert_x == True: # if x axis inverted and cdf => 1-cdf to have the same logic of ascanding ccdf values with ascending on x axis
                    ds = 1- data.sel(time= t)  
                else: 
                    ds = data.sel(time= t)    
                ax.stairs(ds, bins, alpha=0.2, color=color, linewidth=0.8)
        if main:
            if  cdf == True and invert_x == True: 
                mean = 1- data.mean(dim = "time")
            else: 
                mean = data.mean(dim = "time")
            ax.stairs(mean, bins,color=color, linewidth=1.5, label=label)
        if uncertainty:
            
            daily = data.resample(time="1D").mean()  
            
            if cdf == True and invert_x == True:
                daily = 1 - daily
                
            low  = daily.quantile(percentiles[0], dim="time")   
            high = daily.quantile(percentiles[1], dim="time")   
                
            ax.fill_between(data.bin_center.values,low.values,high.values,alpha=0.2,color=color,step="mid",linewidth=0,label = label_uncertainty)

    # add information to plot
    if vlines:
        for xval, lbl, ypos in vlines:
            ax.axvline(xval, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
            ax.text(
                xval * 1.05 if xscale == "log" else xval + 0.5, ypos, lbl,
                color="gray", fontsize=18, va="top", ha="left",
                transform=ax.get_xaxis_transform(),
            )

    # format axis
    ax.set_xscale(xscale)
    if xscale == "log":
        ax.xaxis.set_major_formatter(plt.ScalarFormatter())
        ax.xaxis.get_major_formatter().set_scientific(False)
    ax.set_yscale(yscale)
    # if yscale == "log":
 
    if ylim:
        ax.set_ylim(ylim)
    if cdf: 
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}"))
    if xlim:
        ax.set_xlim(xlim)
        
    if invert_x:
        ax.invert_xaxis()

    # labels
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontweight="bold")
 
    if legend:
        ax.legend(frameon=False)
    sns.despine(ax=ax)
