def quick_lifetime_plot_tracks(plottracks, params = None, title = "Set titel"): 
    """
    One row per track, one column per variable in `params`, plotted against track lifetime (h).
    plottracks: DataFrame with "track", "time_track" (timedelta since initiation) and the columns in `params`.
    params: list of (column, label); default: rain amount, cell/anvil area, min Tb, mean anvil IWP.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    if params is None:                           
        params = [
            ("rain_amount", "Rain amount"),
            ("area_cell", "Cell area"),
            ("area_anvil", "Anvil area"),
            ("min_tb", "Min BT"),
            ("mean_iwp_anvil", "Mean IWP"),]

    tracks = sorted(plottracks["track"].unique())
    
    fig, axes = plt.subplots(
        len(tracks), len(params),
        figsize=(4 * len(params), 3 * len(tracks)),
        sharex="row"
    )
    
    if len(tracks) == 1:
        axes = np.expand_dims(axes, 0)
    
    for i, track in enumerate(tracks):
        df = (
            plottracks[plottracks["track"] == track]
            .sort_values("time_track")
            .copy()
        )
    
        t = df["time_track"].dt.total_seconds() / 3600  # hours since initiation
    
        for j, (var, label) in enumerate(params):
            ax = axes[i, j]
            ax.plot(t, df[var], marker="o", ms=2)
            ax.set_title(label)
            ax.grid(alpha=0.3)
    
            if i == len(tracks) - 1:
                ax.set_xlabel("Track lifetime (h)")
            if j == 0:
                ax.set_ylabel(f"Track {track}")
    
    plt.tight_layout()
    plt.suptitle(title,fontweight = "bold")
    sns.despine()
    plt.show()


####################
def plot_yearly_dev_abs_sorted_by_t(
    data,
    variables,
    variable_name_of_temperature_data,
    var_meta,
    x_label,
    data_low=None,        #  xarray Dataset with ci_low for y-variables
    data_upper=None,      #  xarray Dataset with ci_high for y-variables

    annual_mean_alpha = 10, # alpha of annual mean CI
    slopes = None, # df from csv with slopes, intercept, ci_low, ci_high columns
    plot_ci_slopes = False,
    slope_alpha = 10,
    all_slopes = None, # if all slopes should be plotted 
    all_intercepts = None, # if all slopes should be plotted 
    save=False,
    output_directory=".",
    output_file = "tmp.png",
    title="",
    connect_dots = False):
    """
    Annual means vs. annual-mean temperature (x sorted ascending, coloured by year), all `variables` in one axes.
    data: Dataset (year) with the variables and `variable_name_of_temperature_data`.
    data_low / data_upper: ci_low / ci_high Datasets of the same layout (y error bars; x error bars via the temperature variable).
    var_meta[var]: needs "factor" (y is multiplied by it) and "label_factor" (y label).
    slopes: xr.Dataset indexed by "variable" with "slope", "intercept" (main fit line).
    all_slopes / all_intercepts: DataFrames (n_boot x variable) from calc_slope_perT_fromerr, drawn as grey lines;
    plot_ci_slopes adds the percentile band (slope_alpha in %).
    annual_mean_alpha, slope_alpha: significance levels in %.
    Output: Scatter plot with absolute changes SORTED by t mean per year,
            with optional CI error bars on both axes.
    """
    import matplotlib
    
    plt.figure(figsize=(12, 6))

    sns.set_context("talk")
    

    sort_idx = np.argsort(data[variable_name_of_temperature_data].values)
    data = data.isel(year=sort_idx)
    tas_sorted = data[variable_name_of_temperature_data].values
    

    # Sort CI datasets by the same index
    data_x_low = None
    data_x_upper = None
    
    if data_low is not None:
        data_low = data_low.isel(year=sort_idx)
        data_x_low = data_low[variable_name_of_temperature_data]
    
    if data_upper is not None:
        data_upper = data_upper.isel(year=sort_idx)
        data_x_upper = data_upper[variable_name_of_temperature_data]

    
    # Compute x-axis error bars (tas CI), if available
    if data_x_low is not None and data_x_upper is not None:
        x_err_low  = tas_sorted - data_x_low.values
        x_err_high = data_x_upper.values - tas_sorted
        xerr = np.array([x_err_low, x_err_high])
    else:
        xerr = None

    for var in variables:
        meta = var_meta[var]
        y_vals = data[var].values * meta["factor"]

        # Compute y-axis error bars (variable CI), if available
        if data_low is not None and data_upper is not None:
            y_err_low  = y_vals - data_low[var].values  * meta["factor"]
            y_err_high = data_upper[var].values * meta["factor"] - y_vals
            yerr = np.array([y_err_low, y_err_high])
        else:
            yerr = None

        # Line connecting dots
        if connect_dots is True: 
            plt.plot(tas_sorted, y_vals,
                     '-', color="black", linewidth=0.5, zorder=4)

        # Error bars (plotted before scatter so dots sit on top)
        if xerr is not None or yerr is not None:
            plt.errorbar(
                tas_sorted, y_vals,
                xerr=xerr,
                yerr=yerr,
                fmt='none',          # no marker bc scatter draws those below
                ecolor='gray',
                elinewidth=0.8,
                capsize=3,
                capthick=0.8,
                alpha=0.6,
                zorder=4,
            )

        # Dots colored by year
        sc = plt.scatter(tas_sorted, y_vals,
                         c=data.year.values,   # already sorted
                         cmap='viridis_r' ,#'cividis_r',
                         s=80, zorder=5)

        # add main slopes
        if slopes is not None: 
            intercept = slopes.sel(variable = var)["intercept"].item()
            main_slope = slopes.sel(variable = var)["slope"].item()
            y_vals_slope = (intercept + main_slope * tas_sorted)*meta["factor"]
            plt.plot(tas_sorted, y_vals_slope, '-',color='black',linewidth=2, zorder=3,  label='Main fit')

        # confidence bands
        if plot_ci_slopes is True and all_slopes is not None and all_intercepts is not None:
            lower_p = slope_alpha/2
            upper_p = 100-lower_p
            # compute all bootstrap lines
            boot_lines = np.array([
                (all_intercepts[var].iloc[i] + all_slopes[var].iloc[i] * tas_sorted) * meta["factor"]
                for i in range(len(all_slopes))
            ])
            # take percentiles at each temperature point
            y_lower = np.percentile(boot_lines, lower_p, axis=0)
            y_upper = np.percentile(boot_lines, upper_p, axis=0)
            
            plt.fill_between(tas_sorted, y_lower, y_upper,
                             color='red', alpha=0.2, zorder=2)

        # if all slopes
        if all_slopes is not None and all_intercepts is not None:
            for i in range(len(all_slopes)):
                slope = all_slopes[var].iloc[i]
                intercept = all_intercepts[var].iloc[i]
                y_boot = (intercept + slope * tas_sorted) * meta["factor"]
                plt.plot(tas_sorted, y_boot, '-', color='grey', alpha=0.2, linewidth=0.5, zorder=1)

    # add colorbar for the dots
    plt.colorbar(sc, label='Year')

    # y lims depending on if errorbars are plotted or not
    if xerr is not None or yerr is not None:
        plt.axhline(1, color="gray", linestyle="--", linewidth=1)
        ymin = (np.min(data_low[var]) - 0.01 * np.min(data_low[var])) * meta["factor"]
        ymax = (np.max(data_upper[var]) + 0.01 * np.max(data_upper[var])) * meta["factor"]
        plt.ylim(ymin, ymax)
    else:
        ymin = (np.min(data[var])-0.01*np.min(data[var]))*meta["factor"]
        ymax = (np.max(data[var])+0.01*np.max(data[var]))*meta["factor"]
        ylim = [ymin,ymax]
        plt.ylim(*ylim)



    # legend of lines
    legend_handles = []
    if slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='black', linewidth=2, linestyle='-', label=rf"slope = {main_slope:.3g} K$^{-1}$"))
    if plot_ci_slopes and slopes is not None:
        legend_handles.append(
            matplotlib.patches.Patch(facecolor='red', alpha=0.2, label=f'{slope_alpha}% CI band'))
    if all_slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0.5, linestyle='-',
                       alpha=0.5, label='All bootstrapped Slopes'))
            
    legend_handles.append(
        plt.scatter([], [], c='grey', s=80, label='Annual means'))
    
    if data_low is not None and data_upper is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0, linestyle='none',
                       marker='|', markersize=10, markeredgewidth=1.5,
                       alpha=0.6, label=f'{annual_mean_alpha}% CI') )
    
    if legend_handles:
        # plt.legend(handles=legend_handles, loc='best', frameon=True)
        plt.subplots_adjust(bottom=0.25)
        plt.legend(handles=legend_handles,
           loc='upper center',
           bbox_to_anchor=(0.5, -0.35),
           ncol=len(legend_handles),
           frameon=True)


    # plots format
    sns.despine(right=True, top=True)
    plt.title(title)
    plt.xlabel(f'{x_label}')
    plt.ylabel(meta["label_factor"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    

    # save
    if save:
        output_file = output_file
        plt.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()

######################

#####################################################################################
######## MULTIPANEL SLOPES PER ANNUAL T ### 
#######################################################################################


def plot_yearly_dev_abs_sorted_by_t_multi(
    data,
    variables,
    variable_name_of_temperature_data,
    var_meta,
    x_label,
    data_low=None,        #  xarray Dataset with ci_low for y-variables
    data_upper=None,      #  xarray Dataset with ci_high for y-variables

    annual_mean_alpha = 10, # alpha of annual mean CI
    slopes = None, # df from csv with slopes, intercept, ci_low, ci_high columns
    plot_ci_slopes = False,
    slope_alpha = 10,
    all_slopes = None, # if all slopes should be plotted 
    all_intercepts = None, # if all slopes should be plotted 
    save=False,
    output_directory=".",
    output_file = "tmp.png",
    title="",
    connect_dots = False,
    ncols = 3,
    legendright = False,
    fontscale = 1):
    
    '''
    Like plot_yearly_dev_abs_sorted_by_t, but one panel per variable (ncols columns, panels labelled a), b), ...),
    shared colourbar (right if legendright) and one shared legend. var_meta[var] needs "factor", "unit", "label", "color".
    

    Output: Scatter plot with absolute changes SORTED by t mean per year,
            with optional CI error bars on both axes.
    '''
    import os
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches
    import seaborn as sns
    import numpy as np
    import string
    
    #plt.figure(figsize=(12, 6))

    #sns.set_context("talk")
    

    sort_idx = np.argsort(data[variable_name_of_temperature_data].values)
    data = data.isel(year=sort_idx)
    tas_sorted = data[variable_name_of_temperature_data].values
    

    # Sort CI datasets by the same index
    data_x_low = None
    data_x_upper = None
    
    if data_low is not None:
        data_low = data_low.isel(year=sort_idx)
        data_x_low = data_low[variable_name_of_temperature_data]
    
    if data_upper is not None:
        data_upper = data_upper.isel(year=sort_idx)
        data_x_upper = data_upper[variable_name_of_temperature_data]

    
    # Compute x-axis error bars (tas CI), if available
    if data_x_low is not None and data_x_upper is not None:
        x_err_low  = tas_sorted - data_x_low.values
        x_err_high = data_x_upper.values - tas_sorted
        xerr = np.array([x_err_low, x_err_high])
    else:
        xerr = None

    # plot preparation 
    n = len(variables)
    ncols = ncols
    nrows = int(np.ceil(n / ncols))

    sns.set_context("notebook", font_scale = fontscale)

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), layout = "constrained")
    axes = np.atleast_1d(axes).ravel()

    #for ax, var in zip(axes, variables):
    for panelidx, (ax, var) in enumerate(zip(axes, variables)):
        if var is None or str(var).strip() == "":
            ax.set_visible(False)  # or continue, but see note below
            continue
        meta = var_meta[var]
        y_vals = data[var].values * meta["factor"]
        main_slope = None

        # Compute y-axis error bars (variable CI), if available
        if data_low is not None and data_upper is not None:
            y_err_low  = y_vals - data_low[var].values  * meta["factor"]
            y_err_high = data_upper[var].values * meta["factor"] - y_vals
            yerr = np.array([y_err_low, y_err_high])
        else:
            yerr = None

        # Line connecting dots
        if connect_dots is True: 
            ax.plot(tas_sorted, y_vals,
                     '-', color="black", linewidth=0.5, zorder=4)

        # Error bars (plotted before scatter so dots sit on top)
        if xerr is not None or yerr is not None:
            ax.errorbar(
                tas_sorted, y_vals,
                xerr=xerr,
                yerr=yerr,
                fmt='none',          # no marker bc scatter draws those below
                ecolor='gray',
                elinewidth=0.8,
                capsize=3,
                capthick=0.8,
                alpha=0.6,
                zorder=4,
            )

        # Dots colored by year
        sc = ax.scatter(tas_sorted, y_vals,
                         c=data.year.values,   # already sorted
                         cmap='viridis_r' ,#'cividis_r',
                         s=80, zorder=5)

        # add main slopes
        if slopes is not None: 
            intercept = slopes.sel(variable = var)["intercept"].item()
            main_slope = slopes.sel(variable = var)["slope"].item()
            y_vals_slope = (intercept + main_slope * tas_sorted)*meta["factor"]
            ax.plot(tas_sorted, y_vals_slope, '-',color="black",linewidth=2, zorder=3)

        # confidence bands
        if plot_ci_slopes is True and all_slopes is not None and all_intercepts is not None:
            lower_p = slope_alpha/2
            upper_p = 100-lower_p
            # compute all bootstrap lines
            boot_lines = np.array([
                (all_intercepts[var].iloc[i] + all_slopes[var].iloc[i] * tas_sorted) * meta["factor"]
                for i in range(len(all_slopes))
            ])
            # take percentiles at each temperature point
            y_lower = np.percentile(boot_lines, lower_p, axis=0)
            y_upper = np.percentile(boot_lines, upper_p, axis=0)
            
            ax.fill_between(tas_sorted, y_lower, y_upper,
                             color='red', alpha=0.2, zorder=2)

        # if all slopes
        if all_slopes is not None and all_intercepts is not None:
            for i in range(len(all_slopes)):
                boot_slope = all_slopes[var].iloc[i]
                boot_intercept = all_intercepts[var].iloc[i]
                y_boot = (boot_intercept + boot_slope * tas_sorted) * meta["factor"]
                ax.plot(tas_sorted, y_boot, '-', color='grey', alpha=0.2, linewidth=0.5, zorder=1)

        # y lims depending on if errorbars are plotted or not
        if xerr is not None or yerr is not None:
            ax.axhline(1, color="gray", linestyle="--", linewidth=1)
            ymin = (np.min(data_low[var]) - 0.01 * np.min(data_low[var])) * meta["factor"]
            ymax = (np.max(data_upper[var]) + 0.01 * np.max(data_upper[var])) * meta["factor"]
            ax.set_ylim(ymin, ymax)
        else:
            ymin = (np.min(data[var])-0.01*np.min(data[var]))*meta["factor"]
            ymax = (np.max(data[var])+0.01*np.max(data[var]))*meta["factor"]
            ylim = [ymin,ymax]
            ax.set_ylim(*ylim)

        # per-panel legend: just the slope value
        if main_slope is not None:
            def format_value_maybe_sci(value, threshold_exp=4, sig_figs=3):
                if value == 0:
                    return "0"
                exponent = int(np.floor(np.log10(abs(value))))
                if abs(exponent) < threshold_exp:
                    return f"{value:.3g}"
                mantissa = value / 10**exponent
                return f"{mantissa:.{sig_figs-1}f}$\\times10^{{{exponent}}}$"

            label = rf"{format_value_maybe_sci(main_slope)} {meta['unit']} K$^{{-1}}$"
            legend = ax.legend(
                handles=[plt.Line2D([0], [0], color='black', linewidth=2,
                                     label=label)],
                
                loc='upper left',
                frameon=True,edgecolor = meta["color"],
                facecolor = meta["color"],framealpha=0.2,
            )
            legend.set_zorder(10)
        # plots format
        sns.despine(right=True, top=True)

        ax.set_xlabel(f'{x_label}')
        ax.tick_params(axis='x', rotation=45)

        
        if meta["factor"] == 1:
            ax.set_ylabel(f"{meta['unit']}")
        else: 
            ax.set_ylabel(f"{meta['factor']} * {meta['unit']}")

        from matplotlib.ticker import FuncFormatter
        
        def sci_formatter(x, pos, threshold_exp=4):
            if x == 0:
                return "0"
            exponent = int(np.floor(np.log10(abs(x))))
            if abs(exponent) < threshold_exp:
                # small enough magnitude -> just show it plainly
                return f"{x:g}"
            mantissa = x / 10**exponent
            return f"${mantissa:.1f}\\times10^{{{exponent}}}$"
        
        ax.yaxis.set_major_formatter(FuncFormatter(sci_formatter))

        panel_label = string.ascii_lowercase[panelidx]
        ax.set_title(f"{panel_label}) {meta['label']}", fontweight="bold")
        

    for ax in axes[len(variables):]:
        fig.delaxes(ax)

    ## LEGENED 
    #  shared colorbar 
    if legendright:
       cbar = fig.colorbar(
        sc,
        ax=axes[:len(variables)],
        orientation="vertical",
        location="right",
        fraction=0.04,      # thickness
        pad=0.02,           # distance from subplots
        shrink=1/ncols,
        aspect=35,
    )

    else:
        cbar = fig.colorbar(
            sc,
            ax=axes[:len(variables)],
            orientation="horizontal",
            location="bottom",
            fraction=0.04,      # thickness
            pad=0.02,           # distance from subplots
            shrink=1/ncols,
            aspect=35,
        )
    
    cbar.set_label("Year")
    
    # one full legend for the whole figure
    legend_handles = []
    if slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='black', linewidth=2, linestyle='-', label='Mean Slope')
        )
    if plot_ci_slopes and slopes is not None:
        legend_handles.append(
            matplotlib.patches.Patch(facecolor='red', alpha=0.2, label=f'{slope_alpha}% CI slope')
        )
    if all_slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0.5, linestyle='-', alpha=0.5, label='All bootstrapped Slopes')
        )

    legend_handles.append(
        plt.scatter([], [], c='grey', s=80, label='Annual means')
    )

    if data_low is not None and data_upper is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0, linestyle='none',
                       marker='|', markersize=10, markeredgewidth=1.5,
                       alpha=0.6, label=f'{100-annual_mean_alpha}% CI') )

    
    if legend_handles:
        fig.canvas.draw()

        if legendright: 
            fig.legend(handles=legend_handles,
               loc='upper center',
               bbox_to_anchor=(1, 0.83),
               ncol=1,#len(legend_handles),
               frameon=False)
        else: 
            cbar_pos = cbar.ax.get_position()
            if nrows >= 4:
                legend_y = cbar_pos.y0 - 0.02
            elif nrows == 3: 
                legend_y = cbar_pos.y0 - 0.06   # small fixed gap BELOW the colorbar's actual bottom edge
            elif nrows == 2: 
                legend_y = cbar_pos.y0 - 0.08   # small fixed gap BELOW the colorbar's actual bottom edge
            else: 
                legend_y = cbar_pos.y0 - 0.08   # small fixed gap BELOW the colorbar's actual bottom edge

            fig.legend(handles=legend_handles,
               loc='upper center',
               bbox_to_anchor=(0.5, legend_y),
               ncol=len(legend_handles),
               frameon=False)
            #fig.subplots_adjust(bottom=0.15)

    fig.suptitle(title, fontweight = "bold")    

    # save
    if save:
        output_file = output_file
        fig.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()




######### 

#####################################################################################
##### # slope bar plost 
#######################################################################################

# slopes/ annual data plots 
def plot_slope_comparison(
    ds,
    variable_order,
    variant_order,
    VAR_META,
    colors=None,
    colortype = "variable",
    hatches=None,
    hatchtype = "variable",
    ylabel='Slope (%/K)',
    ylim=(-5, 5),
    title='',
    figsize=(10,5),
    output_path=None, 
    return_ax = False,
    ax_passed = None,
    showCClines = True,
    drawvalues = False,
    legend="variant",          # NEW: "variant" | "hatches" | "both" | None
    xaxislabelscale = 1.3
):
   
    """
    Plot slopes with confidence intervals for multiple variants and variables.
    Labels come from VAR_META.
    ds: Dataset (variant, variable) with slope, slope_ci_lower, slope_ci_upper (absolute bounds; values x100 for plotting, i.e. %/K).  
    VAR_META[var]: "label", "color", optional "hatch".
    colortype: "variable" (VAR_META colours) or "variant" (`colors`: dict variant -> colour, or a list).
    hatchtype: "variable" (VAR_META hatch) or "variant" (`hatches`: dict variant -> hatch).
    showCClines: 7 and 14 %/K reference lines; drawvalues: write values above bars.
    legend: "variant", "hatches" (Cell/Anvil) or False. Draws into ax_passed if given.
    ylabel, ylim, title: plot settings
    output_path: save figure if provided

    Returns fig, or (fig, ax) if return_ax.
    
    
    """

    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import matplotlib.patches as mpatches
    
    
    
    sns.set_context('talk',font_scale = 1.1)
  
    if colors is None:
        colors = plt.cm.Set2.colors
    if hatches is None:
        hatches = {v: '' for v in variant_order}
    
    x = np.arange(len(variable_order))

    width = 0.8 / len(variant_order)
    
    if ax_passed is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax_passed.get_figure()
        ax = ax_passed
    
    
    
    # CC scaling lines
    ax.axhline(7, color='grey', linewidth=1.2, linestyle='--', alpha=0.5,zorder= 0 )#, label='CC',zorder=0) #(~7%/K)
    ax.axhline(14, color='grey', linewidth=1.2, linestyle='--', alpha=0.2,zorder = 0)#, label='2x CC',zorder=0) #(~14%/K)'
    ax.axhline(0, color='grey', linewidth=1.2, linestyle='-', alpha=0.5,zorder=0)

    fontsizelabels_smaller = ax.xaxis.get_ticklabels()[0].get_fontsize() * 1 

    if showCClines:
        ax.annotate("CC",   xy=(1.01, 7),  xycoords=("axes fraction", "data"),
                va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.7, clip_on=False)
        ax.annotate("2×CC", xy=(1.01, 14), xycoords=("axes fraction", "data"),
                va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.5, clip_on=False)


    # slopes per variant
    for i, v in enumerate(variant_order):
        slopes = ds['slope'].sel(variant=v).sel(variable=variable_order)
        lower = slopes - ds['slope_ci_lower'].sel(variant=v).sel(variable=variable_order)
        upper = ds['slope_ci_upper'].sel(variant=v).sel(variable=variable_order) - slopes
        
        slopes_scaled = slopes 
        err = np.array([lower.values, upper.values])

        if colortype == "variable": 
            bar_colors = [VAR_META[var]['color'] for var in variable_order]
        elif colortype == "variant": 
            bar_colors = colors[v] if isinstance(colors, dict) else colors[i % len(colors)]

        if hatchtype== "variable":
            bar_hatches = [VAR_META[var].get('hatch', '') for var in variable_order]   # NEW
        else: 
            bar_hatches = hatches.get(v, '')

        if drawvalues: 
            for var_i, (xi, val, err_up) in enumerate(zip(x + i*width, slopes_scaled.values*100, upper.values*100)):
            #for xi, val, err_up in zip(x + i*width, slopes_scaled.values*100, upper.values*100):
                current_var = variable_order[var_i]
                if current_var in ("PE_anvil", "PE_cell"):
                    offset = 0.03
                else:
                    offset = 0.3
                ax.text(xi, val + err_up + offset, f'{val:.1f}', ha='center', va='bottom', fontsize=fontsizelabels_smaller, zorder=3)
        ax.bar(
            x + i*width,
            slopes_scaled*100,
            width,
            yerr=err*100,
            capsize=4,
            label=v,
            color=bar_colors,
            hatch=bar_hatches,
            alpha=1,
            edgecolor='black',
            zorder=2
        )
    
    # labels
    labels = [VAR_META[var]['label'] for var in variable_order]
    centers = x + (len(variant_order)-1)*width/2
    
    ax.set_xticks(centers)
    ax.set_xticklabels(labels, rotation=45, ha='right',
                      fontsize=ax.xaxis.get_ticklabels()[0].get_fontsize() * xaxislabelscale)  # bump only x labels)
    
    ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim)
    ax.set_title(title,fontweight='bold')

    # legend
    if legend == "variant":
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            frameon=False)

    elif legend == "hatches":
        hatch_label_map = {'': 'Cell', 'xx': 'Anvil'}
        seen = list(dict.fromkeys(VAR_META[var].get('hatch', '') for var in variable_order))
        handles = [mpatches.Patch(facecolor='white', edgecolor='black', hatch=hp) for hp in seen]
        labels = [hatch_label_map.get(hp, hp) for hp in seen]
        ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1.02, 0.5), frameon=False)

    elif legend == False:
        pass

        
    # make up
    sns.despine(right=True, top=True)
    plt.tight_layout()

    # saving options
    if output_path is not None and ax_passed is None:
        plt.savefig(output_path, bbox_inches="tight", pad_inches=0.02)
    if ax_passed is None:
        plt.show()

    if return_ax: 
        return fig,ax
        
    return fig




#######################################
### boxplots 

def quick_boxplots(ds, var_meta_icon, var_meta_obs,
                    vars_to_plot=None, vars_not_plot=["track"], month="JUNE", ncols=3, title = None, 
                   alpha = 0.05,
                  fig = None, axes = None,subplotlabelpre= None,
                  fontsizesubplots = 14):
    """
    Boxplot OBS vs ICON per variable (one panel each); log y for precip/rain/iwp/area/dist variables.
    ds[source][month]: DataFrames, source in {"OBS", "ICON"}. vars_to_plot default: all non-datetime columns except vars_not_plot.
    Title: OBS and ICON median and Δmedian (ICON vs OBS, in %). Returns fig.
    `alpha` is unused.
    """
    import string
    import numpy as np 
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from scipy import stats
    
    if vars_to_plot is None:
        vars_to_plot = [
            var for var in ds["OBS"][month].columns
            if var not in vars_not_plot
            and not pd.api.types.is_datetime64_any_dtype(ds["OBS"][month][var])
        ]
    n = len(vars_to_plot)
    ncols = ncols
    nrows = int(np.ceil(n / ncols))
    
    if fig is None: 
        fig, axes = plt.subplots(nrows, ncols, figsize=(3.5 * ncols, 4.5* nrows), layout = "constrained")
    axes = np.atleast_1d(axes).ravel()
    
    for i, (ax, var) in enumerate(zip(axes, vars_to_plot)):
        if var is None or str(var).strip() == "":
            ax.set_visible(False)  # or continue, but see note below
            continue

        # meta
        meta_icon = var_meta_icon[var]
        meta_obs = var_meta_obs[var]

        color_obs_var = meta_obs["color"]  # defs_application.get_var_color(var, "OBS")
        color_icon_var = meta_icon["color"]  # defs_application.get_var_color(var, "ICON")

        use_log = ("precip" in var.lower() or "rain" in var.lower()      
                   or "iwp" in var.lower() or "area" in var.lower()
                   or "dist" in var.lower())
        if "fraction_convection_rain_volume_anvil" in var.lower(): 
            use_log = False
            
        bp = ax.boxplot(
            [
                ds["OBS"][month][var].dropna(),
                ds["ICON"][month][var].dropna(),
            ],
            tick_labels=["OBS", "ICON"],
            patch_artist=True,
            widths = 0.8,
            whis= 2.5,
            showmeans=True,
            meanline=False,
            meanprops=dict(marker="^",markerfacecolor="darkred",markeredgecolor="darkred",markersize=6,alpha=0.8,),
            flierprops=dict(marker="+", markeredgecolor="black", markersize=4), 
        )
        for patch, color in zip(bp["boxes"], [color_obs_var, color_icon_var]):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
            
        if use_log:                          
            ax.set_yscale("log")
            
        for median in bp["medians"]:
            median.set_color("black")
        
        if var == "min_tb_anvil":
            ax.invert_yaxis()



        # Mean lines


        ax.set_ylabel(meta_icon["unit"])

        ################## label
        # mann withney u test, if median vary!
        obs_vals = ds["OBS"][month][var].dropna()
        icon_vals = ds["ICON"][month][var].dropna()
                
        sig_marker = ""
        
        panel_label = string.ascii_lowercase[i]
       

        obs_median = obs_vals.median()
        icon_median = icon_vals.median()  

        obs_mean = obs_vals.mean()
        icon_mean = icon_vals.mean()   

        def fmt_sig(x, threshold=1e4, sig=2):
            """
            Plain integer below `threshold` (e.g. 2000, 2347, 9999),
            typeset scientific notation (2.1×10^4) at or above it.
            """
            if x == 0:
                return "0"
        
            from math import log10, floor
        
            abs_x = abs(x)
            sign = "-" if x < 0 else ""
        
            if abs_x >= threshold:
                exp = floor(log10(abs_x))
                mantissa = abs_x / (10 ** exp)
                return rf"{sign}${mantissa:.{sig-1}f}\times10^{{{exp}}}$"
            elif abs_x >= 1:
                return f"{sign}{abs_x:.2g}"
            else:
                return f"{sign}{abs_x:.2g}"
            


        pct_diff = 100 * (icon_median - obs_median) / obs_median
        pct_diff_mean = 100*(icon_mean - obs_mean)/obs_mean

        if subplotlabelpre:
            title_str = (f"$\\mathbf{{{subplotlabelpre})}}$ {meta_icon['label']}{sig_marker}\n"
                        f"OBS={fmt_sig(obs_median)}\n"#{obs_median:.2g}\n"
                         f"ICON={fmt_sig(icon_median)}\n"#{icon_median:.2g}\n"
                         f"Δmedian={pct_diff:+.0f}%")
        else:
            title_str = (f"$\\mathbf{{{panel_label})}}$ {meta_icon['label']}{sig_marker}\n"
                         f"OBS={fmt_sig(obs_median)}\n"#{obs_median:.2g}\n"
                         f"ICON={fmt_sig(icon_median)}\n"#{icon_median:.2g}\n"
                         f"Δmedian={pct_diff:+.0f}%")
        ax.set_title(title_str, fontsize = fontsizesubplots)
    

    for ax in axes[len(vars_to_plot):]:
        fig.delaxes(ax)
    fig.suptitle(f"{title}", fontweight = "bold")   
    sns.despine()
    return fig

def quick_boxplots_reduced(ds, var_meta_icon, var_meta_obs,
                    vars_to_plot=None, vars_not_plot=["track"], month="JUNE", ncols=3, title = None, 
                   alpha = 0.05,
                  fig = None, axes = None,subplotlabelpre= None,
                  fontsizesubplots = 14):
    """
    Boxplot OBS vs ICON per variable (one panel each); log y for precip/rain/iwp/area/dist variables.
    ds[source][month]: DataFrames, source in {"OBS", "ICON"}. vars_to_plot default: all non-datetime columns except vars_not_plot.
    Title: OBS and ICON median and Δmedian (ICON vs OBS, in %. Returns fig.
    `alpha` is unused.
    """
    import string
    import numpy as np 
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from scipy import stats
    
    if vars_to_plot is None:
        vars_to_plot = [
            var for var in ds["OBS"][month].columns
            if var not in vars_not_plot
            and not pd.api.types.is_datetime64_any_dtype(ds["OBS"][month][var])
        ]
    n = len(vars_to_plot)
    ncols = ncols
    nrows = int(np.ceil(n / ncols))
    
    if fig is None: 
        fig, axes = plt.subplots(nrows, ncols, figsize=(3.5 * ncols, 3.5* nrows), layout = "constrained")
    axes = np.atleast_1d(axes).ravel()
    
    for i, (ax, var) in enumerate(zip(axes, vars_to_plot)):
        if var is None or str(var).strip() == "":
            ax.set_visible(False)  # or continue, but see note below
            continue

        # meta
        meta_icon = var_meta_icon[var]
        meta_obs = var_meta_obs[var]

        color_obs_var = meta_obs["color"]  # defs_application.get_var_color(var, "OBS")
        color_icon_var = meta_icon["color"]  # defs_application.get_var_color(var, "ICON")

        use_log = ("precip" in var.lower() or "rain" in var.lower()      
                   or "iwp" in var.lower() or "area" in var.lower()
                   or "dist" in var.lower())
        if "fraction_convection_rain_volume_anvil" in var.lower(): 
            use_log = False
            
        bp = ax.boxplot(
            [
                ds["OBS"][month][var].dropna(),
                ds["ICON"][month][var].dropna(),
            ],
            tick_labels=["OBS", "ICON"],
            patch_artist=True,
            widths = 0.8,
            whis= 2.5,
            showmeans=True,
            meanline=False,
            meanprops=dict(marker="^",markerfacecolor="darkred",markeredgecolor="darkred",markersize=6,alpha=0.8,),
            flierprops=dict(marker="+", markeredgecolor="black", markersize=4), 
        )
        for patch, color in zip(bp["boxes"], [color_obs_var, color_icon_var]):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
            
        if use_log:                          
            ax.set_yscale("log")

            if var == "mean_precip_cell_mean":
                from matplotlib.ticker import FixedLocator, ScalarFormatter, NullFormatter
                ax.yaxis.set_major_locator(FixedLocator([12, 16, 20, 24]))
                formatter = ScalarFormatter()
                formatter.set_scientific(False)
                ax.yaxis.set_major_formatter(formatter)
        
                # minor ticks: fixed positions between the majors, no labels
                ax.yaxis.set_minor_locator(FixedLocator([14, 18, 22,26]))
                ax.yaxis.set_minor_formatter(NullFormatter())
            
        for median in bp["medians"]:
            median.set_color("black")
        
        if var == "min_tb_anvil":
            ax.invert_yaxis()


        # Mean lines


        ax.set_ylabel(meta_icon["unit"])

        ################## label
        # mann withney u test, if median vary!
        obs_vals = ds["OBS"][month][var].dropna()
        icon_vals = ds["ICON"][month][var].dropna()
                
        sig_marker = ""
        
        panel_label = string.ascii_lowercase[i]
       

        obs_median = obs_vals.median()
        icon_median = icon_vals.median()  

        obs_mean = obs_vals.mean()
        icon_mean = icon_vals.mean()   

        def fmt_sig(x, threshold=1e4, sig=2):
            """
            Plain integer below `threshold` (e.g. 2000, 2347, 9999),
            typeset scientific notation (2.1×10^4) at or above it.
            """
            if x == 0:
                return "0"
        
            from math import log10, floor
        
            abs_x = abs(x)
            sign = "-" if x < 0 else ""
        
            if abs_x >= threshold:
                exp = floor(log10(abs_x))
                mantissa = abs_x / (10 ** exp)
                return rf"{sign}${mantissa:.{sig-1}f}\times10^{{{exp}}}$"
            elif abs_x >= 1:
                return f"{sign}{abs_x:.0f}"
            else:
                return f"{sign}{abs_x:.2g}"


        pct_diff = 100 * (icon_median - obs_median) / obs_median
        pct_diff_mean = 100*(icon_mean - obs_mean)/obs_mean

        if subplotlabelpre:
            title_str = (f"$\\mathbf{{{subplotlabelpre})}}$ {meta_icon['label']}{sig_marker}\n"
                        # f"OBS={fmt_sig(obs_median)}\n"#{obs_median:.2g}\n"
                        #  f"ICON={fmt_sig(icon_median)}\n"#{icon_median:.2g}\n"
                         f"Δmedian={pct_diff:+.0f}%")
        else:
            title_str = (f"$\\mathbf{{{panel_label})}}$ {meta_icon['label']}{sig_marker}\n"
                         # f"OBS={fmt_sig(obs_median)}\n"#{obs_median:.2g}\n"
                         # f"ICON={fmt_sig(icon_median)}\n"#{icon_median:.2g}\n"
                         f"Δmedian={pct_diff:+.0f}%")
        ax.set_title(title_str, fontsize = fontsizesubplots)
    

    for ax in axes[len(vars_to_plot):]:
        fig.delaxes(ax)
    fig.suptitle(f"{title}", fontweight = "bold")   
    sns.despine()
    return fig




#############
## hisotgram under constrauctu function 



def quick_histograms(ds, var_meta_icon, var_meta_obs,
                     vars_to_plot = None, vars_not_plot = ["track","time"], 
                     density = True,
                     uncertainty = True,percentiles =(0.16,0.84),groupbykey = "M",groupbykey_for_uncertainty = "D",
                     month = "JUNE",nbins = 60, use_log_bins = "default", 
                     ncols = 3,y_label = "pdf", title = None,
                    alpha = 0.05,
                    fig = None, axes = None, subplotlabelpre = None,addspace= None,adaptsizes = True):

    """
    Mean PDFs of cell/anvil variables, OBS vs ICON, one panel per variable. Returns fig.
    ds[source][month]: DataFrames with "time" + variables, source in {"OBS", "ICON"}.
    Line: mean over `groupbykey` periods (default "M") of per-period histograms (density=`density`) on shared bins.
    Bins are chosen by variable name (`use_log_bins` is ignored): log for precip/rain/iwp/area/dist/d_eq,
    integer bins for n_sister/n_children, native step for lifetime, else linear.
    Band: from daily histograms (`groupbykey_for_uncertainty`), per bin
        mean ± 1.96 * (q_high - mean | mean - q_low) / sqrt(N),
    q = daily quantiles at `percentiles` (0.16/0.84), N = number of days with counts in the bin.
    Bins with N < 5 (hard-coded) are masked in band and line. Dashed lines: medians.
    No significance test (Mann-Whitney is commented out, `alpha` unused).
    adaptsizes: sets global plt.rcParams font sizes.
    """
    import string
    import numpy as np 
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from scipy import stats
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    
        
    if vars_to_plot is None:
        vars_to_plot = [
            var for var in ds["OBS"][month].columns
            if var not in vars_not_plot
        ]
    
    n = len(vars_to_plot)
    ncols = ncols
    nrows = int(np.ceil(n / ncols))

    sns.set_context("notebook")

    if adaptsizes:
        # Add near the top of the function, before creating fig/axes
        target_width_in = 6.3          # your \linewidth in inches (~15 cm textwidth)
        fig_width_in = 4 * 3       # matches your existing figsize formula
        scale = fig_width_in / target_width_in  # how much the PDF will be shrunk
    
        plt.rcParams.update({
            "font.size": 12 * scale,
            "axes.titlesize": 12 * scale,
            "axes.labelsize": 10 * scale,
            "xtick.labelsize": 10* scale,
            "ytick.labelsize": 10 * scale,
            "legend.fontsize": 10 * scale,
        })

    if fig is None: 
        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), layout = "constrained")
    axes = np.atleast_1d(axes).ravel()
    
    #for ax, var in zip(axes, vars_to_plot):
    for i, (ax, var) in enumerate(zip(axes, vars_to_plot)):
        if var is None or str(var).strip() == "":
            ax.set_visible(False)  # or continue, but see note below
            continue
        obs_vals = ds["OBS"][month][var].dropna()
        icon_vals = ds["ICON"][month][var].dropna()

        # meta 
        meta_icon = var_meta_icon[var]
        meta_obs = var_meta_obs[var]

        # shared bin edges from the combined range of both datasets
        combined = pd.concat([obs_vals, icon_vals])

        color_obs_var = meta_obs["color"]    
        color_icon_var = meta_icon["color"] 


        # bins
        use_log_bins = ("precip" in var.lower() or "rain" in var.lower()
                        or "iwp" in var.lower() or "area" in var.lower()
                        or "dist" in var.lower() or "d_eq" in var.lower()
                       )

        if "n_sister" in var.lower() or "n_children" in var.lower() or "fraction" in var.lower():
            use_log_bins = False
        
        if use_log_bins:
            bins = np.logspace(np.log10(combined.min()), np.log10(combined.max()), nbins + 1)
        #elif var == "n_sister_cells_max" or var=="n_sister_cells_mean" or  var == "n_sister_cells" or var == "n_children_anvil":
        elif "n_sister" in var.lower() or "n_children" in var.lower():
            bins = np.arange(combined.min(), combined.max() + 2) - 0.5
        elif "lifetime" in var.lower():
            # detect the smallest actual gap between distinct values as the native step
            unique_vals = np.sort(combined.unique())
            step = np.min(np.diff(unique_vals)) if len(unique_vals) > 1 else 1
            bins = np.arange(combined.min(), combined.max() + step, step)
        else:
            bins = np.linspace(combined.min(), combined.max(), nbins + 1)


        ###########
        xmins = []
        xmaxs = []
        for source, color in [("OBS", color_obs_var), ("ICON", color_icon_var)]:
        
            data = ds[source][month][["time", var]].dropna()
            data["groupbykey"] = data["time"].dt.to_period(groupbykey)
            
            if uncertainty: 
                data["groupbykey_for_uncertainty"] = data["time"].dt.to_period(groupbykey_for_uncertainty) 
   
            groupbykey_hists = []
            for _, group in data.groupby("groupbykey"):
                counts, _ = np.histogram(group[var], bins=bins, density=density)
                groupbykey_hists.append(counts)
            
            groupbykey_hists = np.asarray(groupbykey_hists)
            
            mean = groupbykey_hists.mean(axis=0)

            if uncertainty:                
                bin_centers = 0.5 * (bins[:-1] + bins[1:])

                groupbykey_for_uncertainty_hist = []
                for _, group in data.groupby("groupbykey_for_uncertainty"):
                    counts, _ = np.histogram(group[var], bins=bins, density=density)
                    groupbykey_for_uncertainty_hist.append(counts)
            
                groupbykey_for_uncertainty_hist = np.asarray(groupbykey_for_uncertainty_hist)
                

                #median_daily = np.median(groupbykey_for_uncertainty_hist,axis=0) 
                
                low = np.quantile(groupbykey_for_uncertainty_hist, percentiles[0], axis=0) # ppercentiles[0] = 0.16 & groupbykey_for_uncertainty_hist = "D"
                high = np.quantile(groupbykey_for_uncertainty_hist, percentiles[1], axis=0) #p84

   
                # count for each bin how many days have cells
                N = (groupbykey_for_uncertainty_hist > 0).sum(axis=0) 
                N = np.maximum(N, 1)  # ensure no 0 divide

                # standard error
                standard_err_high = 1.96*(high-mean) / np.sqrt(N)
                standard_err_low = 1.96*(mean-low) / np.sqrt(N)
                

                # built CI 
                low_ci  = mean - standard_err_low
                high_ci = mean + standard_err_high

                # mask where too few days have data
                min_days = 5  # QQ decide how many
                mask = N < min_days
                
                low_ci  = np.where(mask, np.nan, low_ci)
                high_ci = np.where(mask, np.nan, high_ci)
                                    

                bin_edges = np.repeat(bins, 2)[1:-1]      # length 2*nbins
                low_stair = np.repeat(low_ci, 2)          # length 2*nbins
                high_stair = np.repeat(high_ci, 2)        # length 2*nbins
                
                ax.fill_between(
                    bin_edges,
                    low_stair,
                    high_stair,
                    color=color,
                    alpha=0.2,
                    linewidth=0,
                    label=f"{source} CI",# {100*percentiles[0]:.0f}–{100*percentiles[1]:.0f}%",
                )



                # plotting (only where at least 5 days have data
                mean = np.where(mask, np.nan, mean)

            valid = np.isfinite(mean)
            if valid.any():
                xmins.append(bins[:-1][valid].min())
                xmaxs.append(bins[1:][valid].max())


            ax.stairs(mean, bins, color=color, linewidth=1.5, label=f"{source} monthly mean")


            
           
        ############ 
        
        # median
        obs_median = obs_vals.median()
        icon_median = icon_vals.median()
        
        ax.axvline(obs_median, color=color_obs_var, linestyle='dashed', linewidth=1,label = "median")
        ax.axvline(icon_median, color=color_icon_var, linestyle='dashed', linewidth=1)


        # x axis
        if xmins and xmaxs:
            ax.set_xlim(min(xmins), max(xmaxs))
        
        if var == "min_tb_anvil":
            ax.invert_xaxis()

        
        if use_log_bins:
            ax.set_xscale("log")
        
            from matplotlib.ticker import ScalarFormatter, LogLocator, FixedLocator, NullFormatter, NullLocator, FuncFormatter
        
            def _sci_tick_format(x, pos=None):
                if x <= 0:
                    return ""
                exponent = int(np.floor(np.log10(abs(x))))
                mantissa = x / 10**exponent
                return rf"${mantissa:.0f}\times10^{{{exponent}}}$"
        
            if var == "mean_precip_cell_mean":
                ax.xaxis.set_major_locator(FixedLocator([12, 16, 20, 24]))
                formatter = ScalarFormatter()
                formatter.set_scientific(False)
                ax.xaxis.set_major_formatter(formatter)
                
                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())
                
            elif var == "max_precip_cell_max":
                ax.xaxis.set_major_locator(FixedLocator([30, 60, 90]))
                formatter = ScalarFormatter()
                formatter.set_scientific(False)
                ax.xaxis.set_major_formatter(formatter)

                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())

            elif var == "max_precip_cell":
                ax.xaxis.set_major_locator(FixedLocator([30, 60, 90]))
                formatter = ScalarFormatter()
                formatter.set_scientific(False)
                ax.xaxis.set_major_formatter(formatter)
                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())

                #### domain

            elif var == "cell_area_sum":  # panel (b): A_tot,cell
                ax.xaxis.set_major_locator(FixedLocator([1e5, 2e5]))
                ax.xaxis.set_major_formatter(FuncFormatter(_sci_tick_format))
                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())
            

            elif var == "rain_volume_cell_sum":
                ax.xaxis.set_major_locator(FixedLocator([1e12, 3e12]))
                ax.xaxis.set_major_formatter(FuncFormatter(_sci_tick_format))

                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())
        
            
            elif var == "anvil_area_sum":  # panel (e): A_tot,anvil
                ax.xaxis.set_major_locator(FixedLocator([3e6, 5e6]))
                ax.xaxis.set_major_formatter(FuncFormatter(_sci_tick_format))

                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())
            
            elif var == "rain_volume_anvil_sum":  # panel (f): V_tot,anvil
                ax.xaxis.set_major_locator(FixedLocator([7e12,1e13]))
                ax.xaxis.set_major_formatter(FuncFormatter(_sci_tick_format))
                # minor ticks: keep the tick marks, but no labels
                ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
                ax.xaxis.set_minor_formatter(NullFormatter())

            #elif var == "anvil_area_sum":
                
        
            else:
                # fallback for every other variable, unchanged
                xlim = ax.get_xlim()
                major_locator = LogLocator(base=10)
                major_ticks_in_view = [t for t in major_locator.tick_values(*xlim) if xlim[0] <= t <= xlim[1]]
        
                if len(major_ticks_in_view) < 1:
                    formatter = ScalarFormatter()
                    formatter.set_scientific(False)
                    ax.xaxis.set_minor_formatter(formatter)



                
        if meta_icon["factor"] == 1:
            ax.set_xlabel(f"{meta_icon['unit']}")
        else: 
            ax.set_xlabel(f"{meta_icon['factor']} * {meta_icon['unit']}")


        # y axis
        ax.set_yscale("log")

        if meta_icon["unit"].strip() in ("-", "", "1"):
            ax.set_ylabel(f'{y_label}')
        else:
            ax.set_ylabel(rf'{y_label} ({meta_icon["unit"]})$^{{-1}}$')
        #ax.set_ylabel(rf'{y_label} ({meta_icon["unit"]}$^{{-1}}$)')
              
        # # mann withney u test, if median vary!        
        # _, p_value = stats.mannwhitneyu(obs_vals, icon_vals, alternative="two-sided")
        # sig_marker = "*" if p_value < alpha else ""
        sig_marker = ""

        if subplotlabelpre: 
            if addspace:
                ax.set_title(f"{subplotlabelpre}) {meta_icon['label']}{sig_marker}{addspace}", fontweight="bold")
            else: 
                ax.set_title(f"{subplotlabelpre}) {meta_icon['label']}{sig_marker}", fontweight="bold")
        else: 
            panel_label = string.ascii_lowercase[i]
            ax.set_title(f"{panel_label}) {meta_icon['label']}{sig_marker}", fontweight="bold")
            
        
        ax.grid(False)
     

        #ax.legend()
        
    # remove unused axes
    for ax in axes[len(vars_to_plot):]:
        fig.delaxes(ax)
    
    #axes[0].legend()
    
    handles, labels = axes[0].get_legend_handles_labels()

    if nrows >=5:
        legend_y = -2
    elif nrows == 4:
        legend_y = -0.02
    elif nrows == 3: 
        legend_y = -0.06   # small fixed gap BELOW the colorbar's actual bottom edge
    elif nrows == 2: 
        legend_y = -0.08   # small fixed gap BELOW the colorbar's actual bottom edge
    elif nrows ==1: 
        legend_y = -1
            
    fig.legend(handles, labels,
               loc="lower center",
               bbox_to_anchor=(0.5, legend_y*2),  # slightly below the plots
               ncol=(len(labels)/2)+1,
               frameon=False)
    


    fig.suptitle(f"{title}", fontweight = "bold")    
    sns.despine()
    
    return fig


