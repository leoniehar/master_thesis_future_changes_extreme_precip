def read_slopes_csv_as_ds(csv_info):
    """
    Read per-experiment slope CSVs into one xarray Dataset.

    Parameters
    ----------
    csv_info : dict
        {variant_label: path_to_csv}. Each CSV needs a "variable" column.

    Returns
    -------
    xr.Dataset
        Indexed by ("variant", "variable"); one data variable per
        remaining CSV column.
    """
    import pandas as pd
    import xarray as xr
    
    dfs = []
    for variant_label, path in csv_info.items():
        df = pd.read_csv(path)
        df['variant'] = variant_label
        dfs.append(df)
    
    # --- concat & convert to xarray ---
    df_all = pd.concat(dfs, ignore_index=True)
    ds = df_all.set_index(['variant', 'variable']).to_xarray()
    
    return ds


def compute_annual_cell_stats(
    cellprops_by_year,
    block_length_days=21,
    n_days_nominal = 365,
    percentiles=(0.05, 0.95),
    n_boot=500,
    seed=42,
    vars_to_exclude=("time", "track"),
    return_boot=False,
    block_length_steps_preset = False,
):
    """
    Annual means and circular moving-block bootstrap CIs of cell properties.

    Assumes 3-hourly data (8 steps/day, hard-coded). Bootstrap blocks start
    at day boundaries and wrap circularly over a nominal year of
    `n_days_nominal` days. The SAME block indices are used for all years and
    variables, so bootstrap replicate b is comparable across years/variables
    (needed for the slope bootstrap). Replicates pool all cell observations
    in the resampled steps and take their mean.

    Note: the point estimate uses all valid steps of the actual year
    (366 days in leap years), while bootstrap replicates are limited to
    the nominal year (365 days).

    Parameters
    ----------
    cellprops_by_year : dict
        {year_str: DataFrame}; one row per cell observation, needs a
        datetime column "time".
    block_length_days : int
        Bootstrap block length in days (ignored if
        block_length_steps_preset is set).
    n_days_nominal : int
        Length of the nominal year used for resampling.
    percentiles : tuple
        Lower/upper CI percentiles, e.g. (0.05, 0.95) -> 90 % CI.
    n_boot : int
        Number of bootstrap replicates per year.
    seed : int
        Random seed.
    vars_to_exclude : tuple
        Columns that are not analysed.
    return_boot : bool
        If True, also return the bootstrap distributions.
    block_length_steps_preset : int or False
        Block length in 3-h steps; overrides block_length_days if set.

    Returns
    -------
    dict of xr.Dataset (float32, dim "year"):
        "mean", "ci_low", "ci_high"
        and, if return_boot=True, "boot" with dims ("year", "boot")
        per variable.
    """
    import numpy as np
    import pandas as pd
    import xarray as xr

    # set seed
    rng = np.random.default_rng(seed)
    # years
    years = sorted(cellprops_by_year.keys(),key=int)

    # Variables
    first_df = cellprops_by_year[years[0]]
    vars_to_plot = [c for c in first_df.columns if c not in vars_to_exclude]

    n_years = len(years)
    n_vars = len(vars_to_plot)

    # Output arrays
    mean_arr = np.full((n_years, n_vars),np.nan,dtype="float64")
    low_arr = np.full((n_years, n_vars),np.nan,dtype="float64")
    high_arr = np.full((n_years, n_vars),np.nan,dtype="float64")

    if return_boot:
        boot_arr = np.full((n_years, n_boot, n_vars),np.nan,dtype="float64")

    # Temporal resolution
    steps_per_day = 8
    block_length_steps = block_length_days * steps_per_day
    
    if block_length_steps_preset:
        block_length_steps = block_length_steps_preset
    
    n_blocks = int(np.ceil(n_days_nominal * steps_per_day / block_length_steps))
    n_steps_nominal = n_days_nominal * steps_per_day

    ### temporal_obs_by_year = {}
    # Generate circular bootstrap block indices ONCE
    bootstrap_indices = []
    
    for b in range(n_boot):
        # draw bootstrap indices ONCE
        starts = ( rng.integers(0, n_days_nominal,size=n_blocks) * steps_per_day)
    
        block_idx = np.concatenate([(start + np.arange(block_length_steps)) % n_steps_nominal for start in starts])
    
        # Make every bootstrap replicate exactly one nominal year
        block_idx = block_idx[:n_steps_nominal]
        bootstrap_indices.append(block_idx)


    # Loop over years
    for y_id, year in enumerate(years):

        df = cellprops_by_year[year].copy()
        year_start = pd.Timestamp(f"{year}-01-01")
        year_end = pd.Timestamp(f"{int(year) + 1}-01-01")
        # Number of days in this year
        n_days = (year_end - year_start).days
        n_steps = n_days * steps_per_day

        # Convert timestamps to 3-hour timestep indices
        step = ((df["time"] - year_start)/ pd.Timedelta(hours=3)).astype("int64")

        valid_actual = step.between(0, n_steps - 1)
        valid_nominal = step.between(0, n_steps_nominal - 1)
        
        df_valid = df.loc[valid_actual].copy()
        steps_nominal = step.loc[valid_nominal].to_numpy()
        
        # Build 3-hour temporal array
        temporal_obs = [[] for _ in range(n_steps_nominal)]
        
        for step_i, values in zip(steps_nominal, df.loc[valid_nominal, vars_to_plot].to_numpy()):
            temporal_obs[step_i].append(values)
    
        # Point estimate
        mean_arr[y_id] = np.nanmean(df_valid[vars_to_plot].to_numpy(),axis=0)


        # bootstrappingf
        boot_means = np.full((n_boot, n_vars),np.nan,dtype="float64")
    
        for b, block_idx in enumerate(bootstrap_indices):
    
            boot_values = []
    
            for idx in block_idx:
                if temporal_obs[idx]:
                    boot_values.extend( temporal_obs[idx])
    
            boot_values = np.asarray(boot_values)
            boot_means[b] = np.nanmean(boot_values,axis=0)
    
        # Bootstrap percentile confidence intervals
        low_arr[y_id] = np.nanquantile(boot_means,percentiles[0],axis=0)
        high_arr[y_id] = np.nanquantile(boot_means,percentiles[1],axis=0)
    
        if return_boot:
            boot_arr[y_id] = boot_means

    # Build xarray datasets
    year_coord = np.array(
        [int(y) for y in years],
        dtype="int64")

    def build_ds(arr):

        data_vars = {
            var: (
                ("year",),
                arr[:, i].astype("float32")
            )
            for i, var in enumerate(vars_to_plot)
        }

        return xr.Dataset(
            data_vars=data_vars,
            coords={"year": year_coord})

    ds_out = {
        "mean": build_ds(mean_arr),
        "ci_low": build_ds(low_arr),
        "ci_high": build_ds(high_arr),
    }

    # Optional bootstrap distributions
    if return_boot:
        boot_ds = xr.Dataset(
            {
            var: (("year", "boot"),boot_arr[:, :, i].astype("float32")) for i, var in enumerate(vars_to_plot)},
            coords={
                "year": year_coord,
                "boot": np.arange(n_boot)
            })

        ds_out["boot"] = boot_ds

    return ds_out



def calc_slope_perT_fromerr(var_means, t_means, var_boot, t_boot, 
                            alpha=0.1):
    """
    Slope of each variable vs. temperature, with CIs from paired bootstrap
    replicates (non-parametric).

    Replicate b of the variables and of T must come from the same block
    resampling (same seed / block settings in compute_annual_cell_stats).
    Non-finite pairs are dropped in the bootstrap fits only.

    Parameters
    ----------
    var_means : xr.Dataset
        Annual means per variable, dim "year" (point-estimate fit).
    t_means : xr.DataArray
        Annual mean temperature, dim "year".
    var_boot : xr.Dataset
        Bootstrap means per variable, dims ("year", "boot").
    t_boot : xr.DataArray
        Bootstrap temperature means, dims ("year", "boot").
    alpha : float
        Significance level (0.1 -> 90 % CI).

    Returns
    -------
    df_results : pd.DataFrame
        Columns: variable, slope_point, intercept_point (fit to annual
        means), slope, intercept (mean over bootstrap fits),
        slope_ci_lower, slope_ci_upper (alpha/2 and 1-alpha/2 quantiles).
    df_all_slopes : pd.DataFrame
        Bootstrap slopes, shape (n_boot, n_vars).
    df_all_intercepts : pd.DataFrame
        Bootstrap intercepts, shape (n_boot, n_vars).
    """
    from sklearn.linear_model import LinearRegression
   # from sklearn.metrics import mean_squared_error
    import pandas as pd
    from scipy.stats import norm
    import numpy as np

    dir_lm = []
    all_slopes = {}  # variable -> list of bootstrap slopes
    all_intercepts = {}

    n_boot = t_boot.sizes["boot"]

    for var in list(var_means.data_vars):
        slopes_boot = []
        intercepts_boot = []
    
        for b in range(n_boot):
        
            # One complete bootstrap replicate across all years
            t_sample = t_boot.isel(boot=b).values.astype(float)
            # Same bootstrap replicate for this variable
            y_sample = var_boot[var].isel(boot=b).values.astype(float)
        
            valid = np.isfinite(t_sample) & np.isfinite(y_sample)
        
            model_boot = LinearRegression().fit(
                t_sample[valid].reshape(-1, 1),
                y_sample[valid])
        
            slopes_boot.append(model_boot.coef_[0])
            intercepts_boot.append(model_boot.intercept_)

        all_slopes[var] = slopes_boot
        all_intercepts[var] = intercepts_boot

        # get mean slope and mean intercept 
        slope_mean = np.mean(slopes_boot)
        intercept_mean = np.mean(intercepts_boot)

        slope_ci_lower, slope_ci_upper = np.quantile(slopes_boot,[alpha / 2, 1 - alpha / 2])

        # point estimate slope 
        t_point = t_means.values.astype(float) 
        y_point = var_means[var].values.astype(float) 

        point_model = LinearRegression().fit(t_point.reshape(-1,1),y_point)
        slope = point_model.coef_[0]
        intercept = point_model.intercept_
        
        dir_lm.append({
            "variable":        var,
            "slope_point": slope, # point estimate
            "intercept_point": intercept,
            # from bootstrapping slopes in CI space
            "slope":slope_mean,
            "intercept": intercept_mean,
            "slope_ci_lower":  slope_ci_lower,
            "slope_ci_upper":  slope_ci_upper,
            # "
        })

    df_results   = pd.DataFrame(dir_lm)
    df_all_slopes = pd.DataFrame(all_slopes)   # shape: (n_boot, n_vars)
    df_all_intercepts = pd.DataFrame(all_intercepts)

    return df_results, df_all_slopes,df_all_intercepts



#### old parametric bootstrao 

def calc_slope_perT_fromerr_para(var_means, t_means, var_ci_low, var_ci_upper, 
                             t_ci_low, t_ci_upper, n_boot=500, alpha=0.1):
    """
    LEGACY: parametric bootstrap of slope vs. T.

    Per year, T and each variable are drawn independently from a normal
    distribution with sigma = (ci_high - ci_low) / (2 * z). Not seeded
    (np.random), so results are not reproducible.
    Superseded by calc_slope_perT_fromerr.

    ... parameter as in calc_slope_per_T_from_err

    Returns
    -------
    df_results : pd.DataFrame
        variable, slope, intercept (bootstrap means), slope_ci_lower/upper,
        and the intercepts belonging to those CI slopes
        (intercept_ci_lower/upper).
    df_all_slopes : pd.DataFrame, shape (n_boot, n_vars)
    df_all_intercepts : pd.DataFrame, shape (n_boot, n_vars)
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    import pandas as pd
    from scipy.stats import norm
    import numpy as np

    dir_lm = []
    all_slopes = {}  # variable -> list of bootstrap slopes
    all_intercepts = {}

    # T array (x axis)
    t_vals     = t_means.values.astype(float)
    t_low      = t_ci_low.values.astype(float)
    t_high     = t_ci_upper.values.astype(float)
    n_years    = len(t_vals)

    # T distri of CI for bootstrapping
    z_score = norm.ppf(1 - alpha / 2)  # to get 1.64 for alpha 10% e.g. 
    t_std  = (t_high - t_low) / (2 * z_score) # ci = mean+- 1.64 * sigma => ci low-ci up / 2 = 1.64 * sigma => umstellen

    for var in list(var_means.data_vars):
        y_vals  = var_means[var].values.astype(float)
        y_low   = var_ci_low[var].values.astype(float)
        y_high  = var_ci_upper[var].values.astype(float)

        # get y distri of CI
        y_std  = (y_high - y_low) / (2 * z_score)
        
        slopes_boot = []
        intercepts_boot = []
        
        for _ in range(n_boot):
            # sample T and var independently, year by year, within CI
            t_sample = np.random.normal(t_vals, t_std)
            y_sample = np.random.normal(y_vals, y_std)
            
            model_boot = LinearRegression().fit(t_sample.reshape(-1, 1), y_sample)
            slopes_boot.append(model_boot.coef_[0])
            intercepts_boot.append(model_boot.intercept_)  

        all_slopes[var] = slopes_boot
        all_intercepts[var] = intercepts_boot

        # get mean slope and mean intercept 
        slope_mean = np.mean(slopes_boot)
        intercept_mean = np.mean(intercepts_boot)

        # pick ci lower/upper slope and corresponding intercept
        # Sort bootstrap samples by slope
        sorted_idx = np.argsort(slopes_boot)
        slopes_sorted     = np.array(slopes_boot)[sorted_idx]
        intercepts_sorted = np.array(intercepts_boot)[sorted_idx]

        # get percentils correpsonding to alpha
        lo_pct = (alpha / 2) * 100          # e.g. 5.0  for alpha=0.10
        hi_pct = (1 - alpha / 2) * 100      # e.g. 95.0 for alpha=0.10
        
        # Pick the pairs at the CI percentile positions
        lo_idx = int(np.floor(lo_pct / 100 * n_boot))
        hi_idx = int(np.ceil(hi_pct / 100 * n_boot)) - 1
        
        slope_ci_lower     = slopes_sorted[lo_idx]
        slope_ci_upper     = slopes_sorted[hi_idx]
        intercept_ci_lower = intercepts_sorted[lo_idx]   # intercept paired with lowest slope
        intercept_ci_upper = intercepts_sorted[hi_idx]   # intercept paired with highest slope

        
        dir_lm.append({
            "variable":        var,
            # from bootstrapping slopes in CI space
            "slope":slope_mean,
            "intercept": intercept_mean,
            "slope_ci_lower":  slope_ci_lower,
            "slope_ci_upper":  slope_ci_upper,
            "intercept_ci_lower":intercept_ci_lower,
            "intercept_ci_upper":intercept_ci_upper})

    df_results   = pd.DataFrame(dir_lm)
    df_all_slopes = pd.DataFrame(all_slopes)   # shape: (n_boot, n_vars)
    df_all_intercepts = pd.DataFrame(all_intercepts)

    return df_results, df_all_slopes,df_all_intercepts
    