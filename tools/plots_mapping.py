def tb_colormap(vmin=200.0, vmed=241.0, vmax=300.0):
    '''
    Creates tb colormap typical of IR BTs.
    from example nbook of tobac: https://github.com/tobac-project/tobac/blob/main/examples/Example_Track_on_Radar_Segment_on_Satellite/Example_Track_on_Radar_Segment_on_Satellite.ipynb
    '''
    import matplotlib.pyplot as plt
    from matplotlib.pyplot import cm as cmaps
    import numpy as np

    nfull = 256

    ngray = int(nfull * (vmax - vmed) / (vmax - vmin))
    ncol = nfull - ngray

    colors1 = plt.cm.gray_r(np.linspace(0.0, 1.0, ngray))
    colors2 = plt.cm.Spectral(np.linspace(0., 0.95, ncol))

    # combine them and build a new colormap
    colors = np.vstack((colors2, colors1))
    mymap = plt.matplotlib.colors.LinearSegmentedColormap.from_list(
        "tb_colormap", colors
    )

    return mymap

def precip_colormap(vmin=0.0, vmax=3.0, dv=0.05):
    """IMERG-style precipitation colormap (Blues), levels vmin..vmax in steps of dv. Returns (cmap, norm, levels)."""

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm


    # levels
    thres = np.arange(vmin, vmax + dv, dv)

    # base colormap (kept simple & explicit)
    cmap = plt.cm.Blues

    # normalization
    norm = BoundaryNorm(thres,ncolors=cmap.N,clip=True)

    return cmap, norm, thres


############################################################
######### faster plots (not mmollweide ###############
###################################################
def plot_tb_map_simple_fast(
    data,
    cmap,
    subplot_shape=(1, 1, 1),
    fig=None,
    draw_bottom_label=True,
    draw_top_label=True,
):
    """
    Tb map (PlateCarree) on subplot `subplot_shape` of `fig`; colorbar label from attrs short_name/units.
    data: 2D DataArray (latitude, longitude). cmap: colormap, e.g. tb_colormap(). Returns ax, pcm.
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import numpy as np
    # Create figure if needed
    if fig is None:
        fig = plt.figure(figsize=(15, 3))
        
 

    ax = ax = fig.add_subplot(subplot_shape[0], subplot_shape[1], subplot_shape[2],projection=ccrs.PlateCarree())

    # Base map
    ax.add_feature(cfeature.COASTLINE, linewidth=0.2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.2)
    
    # Gridlines
    gl = ax.gridlines(
        draw_labels=True,linewidth=0.2,color="grey",
        linestyle="--",x_inline=False,y_inline=False,)

    gl.xlocator = plt.FixedLocator(range(-120, 121, 60))
    gl.ylocator = plt.FixedLocator([-23.5, 0, 23.5])

    # gl.xlabel_style = {"size": 12}
    # gl.ylabel_style = {"size": 12}

    gl.bottom_labels = draw_bottom_label
    gl.top_labels = draw_top_label
    gl.right_labels = False

    # Plot brightness temperature
    pcm = ax.pcolormesh(
        data.longitude,
        data.latitude,
        data,
        cmap=cmap,
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )
    
    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")
    
    # Colorbar
    cbar = fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=1,extend = "both")
    cbar.set_label(f"{short_name} ({units})")#, fontsize=12)

    return ax, pcm

def plot_precip_map_simple_fast(
    data,
    cmap,
    subplot_shape=(1, 1, 1),
    fig=None,
    draw_bottom_label=True,
    draw_top_label=True,
):
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    """Like plot_tb_map_simple_fast for precipitation; values <= 0 masked. `cmap` is the tuple (cmap, norm, levels) from precip_colormap()."""
    
    if fig is None:
        fig = plt.figure(figsize=(15, 3))


    # Mask zero 
    data = data.where(data > 0)
    #data = data.clip(min=0)  # keep zeros as actual values


    # colomap
    cmap, norm, thres = cmap

    # Projection
    ax = fig.add_subplot(subplot_shape[0], subplot_shape[1], subplot_shape[2],projection=ccrs.PlateCarree())

    # Base map
    ax.add_feature(cfeature.COASTLINE, linewidth=0.2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.2)

    # Gridlines
    gl = ax.gridlines(draw_labels=True,linewidth=0.2,color="grey",
        linestyle="--",x_inline=False,y_inline=False,
                     )
    gl.xlocator = plt.FixedLocator(range(-120, 121, 60))
    gl.ylocator = plt.FixedLocator([-23.5, 0, 23.5])
    gl.bottom_labels = draw_bottom_label
    gl.top_labels = draw_top_label
    gl.right_labels = False

    # Plot precipitation
    pcm = ax.pcolormesh(
        data.longitude,
        data.latitude,
        data,
        cmap=cmap,
        norm=norm,
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )

    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")
    
    # Colorbar
    cbar = fig.colorbar(pcm,ax=ax,orientation="vertical",
        pad=0.05,aspect=16,shrink=0.9,ticks=thres[::10], extend = "max")
    cbar.minorticks_off()  # removes the extra small ticks
    cbar.set_label(f"{short_name} ({units})")

    return ax, pcm

def plot_iwp_map_simple_fast(
    data,
    subplot_shape=(1, 1, 1),
    fig=None,
    draw_bottom_label=True,
    draw_top_label=True,
):
    """Like plot_tb_map_simple_fast for IWP; values <= 0 masked, fixed LogNorm 1e-3..1e1, "Blues"."""

    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib.colors import LogNorm


    if fig is None:
        fig = plt.figure(figsize=(15, 3))


    # Mask non-positive values (required for LogNorm)
    data = data.where(data > 0)

    # Projection
    ax = fig.add_subplot(
        subplot_shape[0], subplot_shape[1], subplot_shape[2],
        projection=ccrs.PlateCarree()
    )

    # Base map
    ax.add_feature(cfeature.COASTLINE, linewidth=0.2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.2)

    # Gridlines
    gl = ax.gridlines(
        draw_labels=True, linewidth=0.2, color="grey",
        linestyle="--", x_inline=False, y_inline=False,
    )
    gl.xlocator = plt.FixedLocator(range(-120, 121, 60))
    gl.ylocator = plt.FixedLocator([-23.5, 0, 23.5])
    gl.bottom_labels = draw_bottom_label
    gl.top_labels = draw_top_label
    gl.right_labels = False

    # Plot IWP
    pcm = ax.pcolormesh(
        data.longitude,
        data.latitude,
        data,
        cmap="Blues",
        norm=LogNorm(1e-3, 1e1),
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )

    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")

    # Colorbar
    cbar = fig.colorbar(
        pcm, ax=ax, orientation="vertical",
        pad=0.05, aspect=16, shrink=0.9, extend = "max",
    )
    cbar.set_label(f"{short_name} ({units})")

    return ax, pcm

################ 
### quick summary of plot ssimple fast with tb, precip and iwp)
def summarized_plot(tb,precip,iwp,title): 
    """Three stacked maps (Tb, precipitation, IWP; 2D DataArrays) with a common title. Returns fig."""

    import matplotlib.pyplot as plt
    import plots_mapping
    import seaborn as sns
    import pandas as pd
    
    sns.set_context("poster")
    
    fig = plt.figure(figsize=(20, 10))
    
    plot_tb_map_simple_fast(tb, tb_colormap(), subplot_shape=(3,1,1),draw_bottom_label=False, fig=fig)
    plot_precip_map_simple_fast(precip, cmap= precip_colormap(), subplot_shape=(3,1,2), draw_top_label= False,draw_bottom_label=False,fig = fig)
    plot_iwp_map_simple_fast(iwp,subplot_shape=(3, 1, 3),draw_top_label=False,fig=fig)
    
    fig.suptitle(title,fontweight='bold', x=0.5)

    return fig

def title_time_format(dataarraywithtime):
    """Time coordinate as "YYYY-MM-DD HH:MM" (first value if it is an array)."""

    import pandas as pd
    time = pd.to_datetime(dataarraywithtime.time.values)
    if isinstance(time, pd.Timestamp):  # scalar
        return time.strftime("%Y-%m-%d %H:%M")
    else:                               # array
        return time.strftime("%Y-%m-%d %H:%M")[0]


####################################
####### tobac outputs maps #######
def domain_plot_seg_mask(seg2d, domain= [-30, 30, -30, 30],left_grid_label=True,bottom_grid_label = True, figsize=(15, 10),cmap = None,norm= None,background = None,cmap_background = None, title = "", fig = None,ax = None,alpha=1.0):
    """
    Segmentation mask map for domain = [lon_min, lon_max, lat_min, lat_max].
    seg2d: 2D DataArray (latitude, longitude), 0 = background. Default cmap: random (unseeded) colours;
    use build_id_cmap for consistent colours. Optional `background` field (cmap_background).
    Draws into ax if fig and ax are given. Returns fig, ax, gl.
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import cartopy.crs as ccrs
    import numpy as np
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
  
    import seaborn as sns
    sns.set_context("talk")

    lon_min, lon_max, lat_min, lat_max = domain

    # reduce data 
    seg2d = seg2d.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max)
    )
  
    
    lats = seg2d.latitude.values
    lons = seg2d.longitude.values
    
    
    cell_ids = np.unique(seg2d.values)
    cell_ids = cell_ids[cell_ids != 0]  # exclude background
    n_cells = len(cell_ids)

    
    # Map each cell ID to a unique shuffled color
    if cmap is None:
        colors = plt.get_cmap("hsv")(np.linspace(0, 1, n_cells))
        np.random.shuffle(colors)  # shuffle so adjacent IDs don't get similar colors
        
        # Build ListedColormap: index 0 = black (background), rest = shuffled colors
        all_colors = np.vstack([[1, 1, 1, 0], colors]) #(RGBA for background, rest of the colors 
        cmap = mcolors.ListedColormap(all_colors)

    # if no fig or ax are passed
    figisselfcreated = False 
    
    if fig is None or ax is None:
        figisselfcreated = True
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())  # <-- use ax, not plt.axes()

    # Background
    if background is not None:
        background = background.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max))
        pcm = ax.pcolormesh(
            background.longitude,
            background.latitude,
            background,
            cmap=cmap_background,
            transform=ccrs.PlateCarree(),
            shading="auto",
            rasterized=True
        )



    cf = ax.pcolormesh(
        lons, lats, seg2d,
        cmap=cmap,
        norm=norm, 
        alpha=alpha,
        transform=ccrs.PlateCarree(),
        shading='auto',
        rasterized=True
    )

    # --- Gridlines with lat/lon labels ---
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels = True,
        linewidth=0.6,
        color='gray',
        alpha=0.2,
        linestyle='--'
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_grid_label
    gl.bottom_labels = bottom_grid_label
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlabel_style = {'size': 10}
    #gl.ylabel_style = {'size': 10}
    
    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=1)

    ax.set_title(title, fontweight="bold")
    
    #plt.colorbar(cf, label='Segmentation ID', ax=ax, shrink=0.6, aspect=20)
    if figisselfcreated is True:
        plt.show()

    return fig,ax, gl



def format_dict(d: dict, max_chars: int = 28) -> str:
    """Format a dict as compact key:value lines, truncating long values."""
    lines = []
    for k, v in d.items():
        line = f"  {k}: {v}"
        if len(line) > max_chars:
            line = line[:max_chars - 1] + "…"
        lines.append(line)
    return "\n".join(lines)


def add_para_selection_info(fig, **sections):
    """
    Add the given sections (dict or str, None skipped) as a monospace text box right of the figure;
    shrinks the plot area (right=0.75). 
    
    Call like: <keep your existing example>
    add_para_selection_info(
        fig,
        filter_detection_threshold=filter_detection_threshold,
        feature_detection_params=feature_detection_params,
        parameters_segmentation=parameters_segmentation,
    )
    """

    blocks = [] # array to save what is printed

    for name, value in sections.items(): #sections collects every addiontional arguemnt into dict => name and value called with section.items()
        if value is None:
            continue

        if isinstance(value, dict): # if value is dict=> format if not string
            formatted = format_dict(value)
        else:
            formatted = str(value)
 
        blocks.append(f"{name}:\n{formatted}") # add to what is printe 

    if not blocks:
        return

    param_text = "\n\n".join(blocks) # join all block to print

    # 1. Make room on the right side of the figure for the text box
    fig.subplots_adjust(right=0.75)  # shrink plot area; tune this value to your needs

    # 2. Place text in figure coords, just outside the plot (x > right margin)
    fig.text(
        0.77,           # x in figure coords — just past the right=0.75 boundary
        0.5,            # vertically centred
        param_text,
        transform=fig.transFigure,
        fontsize=6,
        verticalalignment="center",
        horizontalalignment="left",
        family="monospace",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="white",
            alpha=0.9,
            edgecolor="gray",
            linewidth=0.6,
        ),
        zorder=100,
        clip_on=False,  # 3. prevents clipping at figure boundary
    )

####################
###### domain plots for tb and preicp #####
##################

def domain_plot_tb(data, domain=[-30, 30, -30, 30], left_grid_label=True,bottom_grid_label = True,figsize = (15, 10) ,title="", fig=None, ax=None,vmin=200, vmed=241, vmax=300,shrink=0.8):
    """
    Plot brightness temperature on a domain subplot
    like  domain_plot_seg_mask 
    possible to use in multipanel
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import seaborn as sns
    sns.set_context("talk")

    figisselfcreated = False
    if fig is None or ax is None:
        figisselfcreated = True
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())

    #cmap = tb_colormap()
    cmap = tb_colormap(vmin=vmin, vmed=vmed, vmax=vmax)
    
    # reduce data 
    lon_min, lon_max, lat_min, lat_max = domain

    data = data.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max)
    )
    
    pcm = ax.pcolormesh(
        data.longitude, data.latitude, data,
        cmap=cmap,
        vmin=vmin, vmax=vmax,
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )

    gl = ax.gridlines(
        crs=ccrs.PlateCarree(), draw_labels = True,
        linewidth=0.6, color='gray', alpha=0.2, linestyle='--'
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_grid_label
    gl.bottom_labels = bottom_grid_label
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlabel_style = {'size': 10}
    #gl.ylabel_style = {'size': 10}

    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=1)
    ax.set_title(title, fontweight="bold")
    
    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")
    
    # Colorbar
    cbar = fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=shrink, extend = "both")
    cbar.set_label(f"{short_name} ({units})")#, fontsize=12)


    if figisselfcreated:
        plt.show()

    return fig, ax, gl


def domain_plot_precip(data, vmin = 0, vmax = 3, domain=[-30, 30, -30, 30],left_grid_label=True,bottom_grid_label = True, figsize = (15, 10), title="", fig=None, ax=None,shrink=0.8):
    """
    Plot precip on a domain subplot
    like  domain_plot_seg_mask 
    possible to use in multipanel
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import seaborn as sns
    import numpy as np
    sns.set_context("talk")

    figisselfcreated = False
    if fig is None or ax is None:
        figisselfcreated = True
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())

    # Mask zeros, get colormap
    data = data.where(data > 0)
    cmap, norm, thres = precip_colormap(vmin,vmax,0.05)
    
    # reduce data 
    lon_min, lon_max, lat_min, lat_max = domain

    data = data.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max)
    )

    pcm = ax.pcolormesh(
        data.longitude, data.latitude, data,
        cmap=cmap, norm=norm,
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )

    gl = ax.gridlines(
        crs=ccrs.PlateCarree(), draw_labels = True,
        linewidth=0.6, color='gray', alpha=0.2, linestyle='--'
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_grid_label
    gl.bottom_labels = bottom_grid_label
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlabel_style = {'size': 10}
    #gl.ylabel_style = {'size': 10}

    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=1)
    ax.set_title(title, fontweight="bold")

    
    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")

    ticks = np.linspace(thres.min(), thres.max(), 6)  # or 4/6 depending on space
    # colorbar
    cbar = fig.colorbar(pcm,ax=ax,orientation="vertical",
        pad=0.05,aspect=16,shrink=shrink,ticks=ticks,extend ="max")
    cbar.minorticks_off()  # removes the extra small ticks
    cbar.set_label(f"{short_name} ({units})")

    

    if figisselfcreated:
        plt.show()

    return fig, ax, gl


def domain_plot_iwp(data, vmin = 1e-3, vmax = 1e1, domain=[-30, 30, -30, 30],left_grid_label=True,bottom_grid_label = True, figsize = (15, 10), title="", fig=None, ax=None,shrink=0.8,):
    """
    Plot iwp on a domain subplot
    like  domain_plot_seg_mask 
    possible to use in multipanel
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    from matplotlib.colors import LogNorm
    import seaborn as sns
    
    sns.set_context("talk")

    figisselfcreated = False
    if fig is None or ax is None:
        figisselfcreated = True
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())


    # Mask zeros, get colormap
    data = data.where(data > 0)
    cmap, norm, thres = precip_colormap(vmin,vmax,0.05)

    # reduce data 
    lon_min, lon_max, lat_min, lat_max = domain

    data = data.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max)
    )

    pcm = ax.pcolormesh(
        data.longitude, data.latitude, data,
        cmap="Blues",
        norm=LogNorm(vmin, vmax),
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True)


    gl = ax.gridlines(
        crs=ccrs.PlateCarree(), draw_labels=True,
        linewidth=0.6, color='gray', alpha=0.2, linestyle='--'
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_grid_label
    gl.bottom_labels = bottom_grid_label
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER


    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=1)
    ax.set_title(title, fontweight="bold")

    
    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")

     # Colorbar
    cbar = fig.colorbar(
        pcm, ax=ax, orientation="vertical",
        pad=0.05, aspect=16, shrink=shrink, extend = "max",
    )
    cbar.set_label(f"{short_name} ({units})")

    

    if figisselfcreated:
        plt.show()

    return fig, ax, gl

##########################################
###### colormap for seg masks ####
#############################

def build_id_cmap(seg_list, seed=0):
    """
    Colormap + BoundaryNorm with one fixed (seeded) random colour per segmentation ID over all masks in `seg_list`,
    so IDs keep their colour across panels; 0 is transparent. Returns cmap, norm.
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    all_ids = np.unique(np.concatenate([np.unique(seg.values) for seg in seg_list]))
    all_ids = all_ids[all_ids != 0]
    n_ids = len(all_ids)

    rng = np.random.default_rng(seed)
    colors = plt.cm.hsv(np.linspace(0, 1, n_ids))
    rng.shuffle(colors)

    # Map ID -> color via a dict
    id_to_color = {cid: colors[i] for i, cid in enumerate(all_ids)}

    # Build colormap + norm over all IDs (including 0 as transparent)
    all_levels = np.concatenate([[0], all_ids])          # 0 = background
    all_colors = [[1, 1, 1, 0]] + [id_to_color[cid] for cid in all_ids]

    cmap = mcolors.ListedColormap(all_colors)
    norm = mcolors.BoundaryNorm(
        boundaries=np.concatenate([all_levels, [all_levels[-1] + 1]]),
        ncolors=len(all_colors)
    )

    return cmap, norm


####################
### plots cells/tracks ###
############
def domain_plot_cells(
    Tracks,
    columntoselect,
    dateselected = None,
    date_start = None,
    date_end = None, 
    domain=[-180, 180, -30, 30],
    figsize=(12, 4),
    left_grid_label=True,
    bottom_grid_label=True,
    draw_top_label=False,
    background=None,
    cmap_background=None,
    title=None,
    fig=None,
    ax=None,
):
    '''
    Plot tobac cell tracks of a selected date, or timeperiod, otherwise all
    created form function in 50_link
    Tracks crossing the dateline (|Δlon| > 180) are skipped.
    
    Tracks        : tobac Tracks DataFrame with columns cell, time, longitude, latitude
    dateselected  : str or pd.Timestamp, timestep to plot
    domain        : [lon_min, lon_max, lat_min, lat_max]
    Returns fig, ax, gl.
    '''
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import numpy as np
    import seaborn as sns
    sns.set_context("talk")

    lon_min, lon_max, lat_min, lat_max = domain

    # select data based on date / date range
    if dateselected: 
        cells_at_time = Tracks.loc[Tracks["time"] == dateselected,columntoselect].unique()
        selected = Tracks[Tracks[columntoselect].isin(cells_at_time)]
        
        title_str = title if title is not None else str(dateselected)
    elif date_start is not None and date_end is not None:
        # selected = Tracks[
        #     (Tracks['time'] >= pd.Timestamp(date_start)) &
        #     (Tracks['time'] <= pd.Timestamp(date_end))
        # ]

        cells_in_window = Tracks.loc[(Tracks["time"] >= date_start) & (Tracks["time"] <= date_end),columntoselect].unique()
        selected = Tracks[Tracks[columntoselect].isin(cells_in_window)]
        
        title_str = title if title is not None else f"Tracks between {date_start} and {date_end}"
    else:
        selected = Tracks
        title_str = title if title is not None else f"All tracks"


    
    figisselfcreated = False
    if fig is None or ax is None:
        figisselfcreated = True
        fig, ax = plt.subplots(figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})
        

    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=0.2)

    # background field (optional)
    if background is not None:
        background_sel = background.sel(
            longitude=slice(lon_min, lon_max),
            latitude=slice(lat_min, lat_max)
        )
        ax.pcolormesh(
            background_sel.longitude,
            background_sel.latitude,
            background_sel,
            cmap=cmap_background,
            transform=ccrs.PlateCarree(),
            shading='auto',
            rasterized=True,
        )

    # gridlines
    gl = ax.gridlines(
        draw_labels=True, linewidth=0.2, color='grey',
        linestyle='--', x_inline=False, y_inline=False,
    )
    gl.xlocator = plt.FixedLocator(range(-180, 181, 60))
    gl.ylocator = plt.FixedLocator([-23.5, 0, 23.5])
    gl.top_labels = draw_top_label
    gl.bottom_labels = bottom_grid_label
    gl.left_labels = left_grid_label
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    # plot tracks
    for cell_id, track in selected.groupby('cell'):
        lons = track.sort_values('time')['longitude'].values
        lats = track.sort_values('time')['latitude'].values
        if np.any(np.abs(np.diff(lons)) > 180):
            continue
        ax.plot(lons, lats, transform=ccrs.PlateCarree(), lw=1.5, alpha=1)

    #title_str = title if title is not None else str(dateselected)
    ax.set_title(title_str, fontweight='bold')

    if figisselfcreated:
        plt.tight_layout()
        plt.show()

    return fig, ax, gl



###########################
###### domain plot tas ##
#################
def domain_plot_tas(data, domain=[-30, 30, -30, 30], left_grid_label=True,bottom_grid_label = True,figsize = (15, 10) ,title="", fig=None, ax=None,vmin=270, vmax=330,shrink=0.8):
    """
    Plot tas
    like  domain_plot_seg_mask 
    possible to use in multipanel
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import seaborn as sns
    sns.set_context("talk")

    figisselfcreated = False
    if fig is None or ax is None:
        figisselfcreated = True
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())

    #cmap = tb_colormap()
    cmap = "Spectral_r"
    
    # reduce data 
    lon_min, lon_max, lat_min, lat_max = domain

    data = data.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_min, lat_max)
    )
    
    pcm = ax.pcolormesh(
        data.longitude, data.latitude, data,
        cmap=cmap,
        vmin=vmin, vmax=vmax,
        transform=ccrs.PlateCarree(),
        shading="auto",
        rasterized=True
    )

    gl = ax.gridlines(
        crs=ccrs.PlateCarree(), draw_labels = True,
        linewidth=0.6, color='gray', alpha=0.2, linestyle='--'
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_grid_label
    gl.bottom_labels = bottom_grid_label
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlabel_style = {'size': 10}
    #gl.ylabel_style = {'size': 10}

    ax.set_extent(domain, crs=ccrs.PlateCarree())
    ax.coastlines(color='grey', linewidth=1)
    ax.set_title(title, fontweight="bold")
    
    # label
    units = data.attrs.get("units")
    short_name = data.attrs.get("short_name")
    
    # Colorbar
    cbar = fig.colorbar(pcm, ax=ax, orientation="vertical", shrink=shrink, extend = "both")
    cbar.set_label(f"{short_name} ({units})")#, fontsize=12)


    if figisselfcreated:
        plt.show()

    return fig, ax, gl