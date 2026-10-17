# Future Changes of Extreme Tropical Precipitation Cells and their Anvils from a Global Storm-Resolving Simulation

> **Leonie Marie Hartog - University of Leipzig Institute of Meteorology / Leibniz Institute for Tropospheric Research - 2026**

This repository contains the code used to create the material of the Master's thesis **"Future Changes of Extreme Tropical Precipitation Cells and their Anvils from a Global Storm-Resolving Simulation"**. 
## Contents 

1. Prerequisites
2. Output data access
3. Workflow overview
	a. plots (based on output data, see 2.)
	b. data (reproduce output data, see 2.)
4. Running notebooks as runners (HPC)
5. Folder structure
6. Notebook overview
7. Tools overview
8. Data sources, citation, contact

## 1. Prerequisites

- **Environment:** 
	- `environment.yml` with the Python 3.11 packages (e.g. tobac, xarray, pandas, numpy, earthaccess, ccic)
		- including tobac 1.6.3 (Tracking and Object-Based Analysis of Clouds) (Heikenfeld et al. 2019)
		- use `environment-full.yml` in case of problems
- **NASA Earthdata account:** required for every notebook that loads IMERG or NASA Tb (OBS) data. The token has to be refreshed regularly (approx. every 6 weeks).
    - See [https://github.com/nasa/gesdisc-tutorials/blob/main/notebooks/How_to_Generate_Earthdata_Prerequisite_Files.ipynb](https://github.com/nasa/gesdisc-tutorials/blob/main/notebooks/How_to_Generate_Earthdata_Prerequisite_Files.ipynb)
- **HPC with SLURM** (only for the runner steps): the starters submit jobs via `sbatch`.
- **external datasets**: (accessed via tools **"handle_ICON_data"**, **"handle_OBS_data"**)
	- see below for more infos, and in `nbooks_plotting/12` for more infos about how they were accessed
	- ICON *ngc4008* (production run NextGEMS) (Segura et al. 2025)
	- NCEP/CPC L3 Half Hourly 4km Global (60S 60N) Merged IR V1 (NASA-Tb) (Janowiak et al. 2017)
	- GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07  (Huffman et al. 2023)
	- Chalmers Cloud Ice Climatology CPCIR (Amell et al. 2024)
- **Data output/input**
	- Check/adapt input path in the nbooks
	- **IMERG reference grid:**  It is required for any execution of notebooks that load OBS data.
		- either: run **`04`** (save IMERG grid as reference) once.
		- or: get the `./output/aux/imerg_grid.nc` file from Output data 
## 2. Output data access
- All data created/ reloaded within the notebooks/ scripts is published on XXQQ (add zenodo link). 
	- exception: output from application of `29` and `50` to the full 30 years of ICON. Only used as intermediate outputs and only used `58`, whose output is accessible


## 3a. Workflow of plot reproduction
- *for plots within nbook_plotting*
	- everything before final dataframes (`60/62`) incl. input layer comparison (`43`)
	- you can use environment.yaml (prerequist), but a standard environment with matplotlib, pandas, xarray, seaborn should also work
	- download corresponding data from zendodo (varies between the nbooks)
	- adapt input paths in nbook
- *for plots within nbook_plotting_2*
	- Evaluation & change assessment
	- you can use environment.yaml (prerequisite), but a standard environment with matplotlib, pandas, xarray, seaborn should also work
	- download data from zendodo (`final_dataframes`, `annual/data` and `annual/slopes`)
	- adapt input paths in nbook
## 3b. Workflow overview for reproduction of data creation

0.  Fullfill Prerequisites

**input layer**
- Exploratory data analysis `06` (=plotted in nbooks_plotting/07)
- Input layer comparison `42`  (=plotted in nbooks_plotting/43)

**Monthly datasets (June & December 2023, ICON and OBS)**
1. Segmentation: `27` (OBS), `28` (ICON), each run with timestamp lists for June and December
2. Linking: `51` (executed separately per monthly dataset)
3. Filtering: `53` (one run for all four monthly datasets)
4. Cell properties / final datasets: `60`
	- saved to `output/final_dataframes/` (2. Output data access)
		-  (=plotted in nbooks_plotting_2/)

- additional 
	- Characterization of the dataset/ rian amount: `55` (ICON), `56` (OBS), `57` (compile outputs of 56) (used in `54`)

**ICON full (30 years)**
1. Segmentation: `29`
2. Add near-surface temperature (tas): `50`
3. Linking & filtering: `58`
4. Cell properties / final datasets: `62`
	- saved to `output/final_dataframes/FULL` (2. Output data access)
5. Annual means (`70`), and slopes (`71`) 
	- saved to `output/annual/` (2. Output data access)
		-  (=plotted in nbooks_plotting_2/)

## 4. Running notebooks as runners (HPC)

For long or large jobs, notebooks are not run interactively but in parallel:

1. A **starter** (`starters/`) converts the notebook to a Python script, saves it in `runner_scripts/`, makes it executable and submits the matching **runner** (`runner/`) to SLURM.
	- when reproducing: adapt the environment in the runner!
2. The runner processes the timestamps from the lists in `runner_scripts/` in parallel (e.g. `timestamps_june.lst`, `timestamps_december.lst`).

```bash
# example 
bash starters/convert_run_nbook27.sh
```


## 5. Folder structure

| Folder               | Content                                                                                                                                                                                                              |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nbooks/`            | Main data processing notebooks: preprocessing, input layer comparison, segmentation, linking, property calculation, i.e. everything up to the creation of the final datasets + annual means/ slopes in `70` and `71` |
| `nbooks_plotting/`   | Plots belonging to `nbooks/` until `62` (exploratory data analysis observations, input layer, segmentation examples, linking effects)                                                                                |
| `nbooks_plotting_2/` | Evaluation and change assessment based on the final dataframes created in `60` and `62`  + annual means/ slopes in `70` and `71`                                                                                     |
| `nbooks_additional/` | Old, experimental and deprecated notebooks (not needed to reproduce the thesis)                                                                                                                                      |
| `output/`            | All outputs of the notebooks and runners (see table below)                                                                                                                                                           |
| `runner/`            | Shell scripts for parallelization                                                                                                                                                                                    |
| `runner_scripts/`    | Python scripts (converted automatically from the notebooks by the starter) and lists of timestamps etc. used as runner input                                                                                         |
| `starters/`          | Bash wrapper scripts: convert a notebook to a script, make it executable and submit the runner to SLURM                                                                                                              |
| `tools/`             | Modules used throughout the analysis                                                                                                                                                                                 |

### `output/` subfolders

| Folder                                   | Content                                                                                                                                                                |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `annual/`                                | Annual mean datasets, slopes, bootstrap sensitivity analysis `70`, `71`                                                                                                |
| `apply_seg/`                             | Tobac segmentations. `apply_ICON` / `apply_OBS` hold the final calculations. Plots and saved masks from interactive notebook are in folders with suffix `_interactive` |
| `aux/`                                   | IMERG reference grid, rain amount from the input layers (`55`, `56`, and `57`)                                                                                         |
| `cdf/`                                   | Input layer comparison (histogram data) `42`                                                                                                                           |
| `EDA_OBS/`                               | Exploratory data analysis of OBS                                                                                                                                       |
| `final_dataframes/`                      | Final dataframes with cell properties: June & December 2023 (ICON/OBS) and ICON full simulation                                                                        |
| `inputparameter_tryout_selection_tobac/` | Input parameter selection (data, tables, figures to review)                                                                                                            |
| `linking/`                               | `filtered/`: all final linked cells. `raw/` and `valid/`: intermediate steps for June and December 2023                                                                |
| `plots/`                                 | Plots                                                                                                                                                                  |
| `zzz_old/`                               | Old material, not to be uploaded                                                                                                                                       |


## 6. Notebook overview

**Runner/starter column:** A number indicates that the notebook can be converted to a script and run in parallel via a starter and runner, (see below).

**Notebook numbering:** `0x` = data access/preparation, `2x` = segmentation, `4x` = input layer comparison, `5x` = linking, rain amount, filtering, `6x` = final datasets, `7x` = change assessment
- nbooks_plotting_2 starts new numbering
### `nbooks/`

| Nbook               | Purpose                                                                                              | Runner | Related dataset / thesis step    |
| ------------------- | ---------------------------------------------------------------------------------------------------- | ------ | -------------------------------- |
| `00`                | Create earthaccess token file                                                                        | no     | Prerequisite for all OBS loading |
| `04`                | Save IMERG grid as reference                                                                         | no     | Prerequisite for all OBS loading |
| `06`                | Count missing timestamps per pixel                                                                   | 06     | exploratory data analysis OBS    |
| `23_interactive`    | OBS segmentation workflow incl. PE                                                                   | no     | Segmentation OBS (development)   |
| `23_inputparameter` | OBS segmentation workflow used for input parameter selection (no PE, no warm BT feature exploration) | 23     | Input parameter selection OBS    |
| `25_interactive`    | ICON segmentation workflow incl. PE                                                                  | no     | Segmentation ICON (development)  |
| `25_inputparameter` | ICON segmentation workflow used for input parameter selection (no PE)                                | 25     | Input parameter selection ICON   |
| `27`                | Apply OBS segmentation workflow                                                                      | 27     | June & December OBS (final)      |
| `28`                | Apply ICON segmentation workflow                                                                     | 28     | June & December  ICON (final)    |
| `29`                | Apply ICON segmentation workflow                                                                     | 29     | ICON full, 30 years (final)      |
| `42`                | PDF and CDF calculation for input layer comparison                                                   | 42     | Input layer comparison           |
| `50`                | Add tas to ICON full                                                                                 | 50     | ICON full                        |
| `51`                | Link cell features                                                                                   | no     | June & December ICON / OBS       |
| `53`                | Filter tracks                                                                                        | no     | June & December ICON / OBS       |
| `54`                | Explore what the monthly datasets represent (needs data from 55, 56, 57)                             | no     | June & December ICON / OBS       |
| `55`                | Rain amount from ICON input images                                                                   | no     | June & December (ICON)           |
| `56`                | Rain amount from OBS input images                                                                    | 56     | June & December  (OBS)           |
| `57`                | Compile outputs of 56                                                                                | no     | June & December  (OBS)           |
| `58`                | Link features & filter tracks (equivalent of 51 + 53)                                                | 58     | ICON full                        |
| `60`                | Create final datasets, property calculation                                                          | no     | June & December ICON / OBS       |
| `62`                | Create final datasets, property calculation                                                          | 62     | ICON full                        |
| `70`                | Bootstrapped annual means                                                                            | no     | Change assessment ICON full      |
| `71`                | Slope calculation (based on bootstrap samples from 70)                                               | no     | Change assessment ICON full      |

### `nbooks_plotting/`

| Nbook         | Purpose                                                      |
| ------------- | ------------------------------------------------------------ |
| `07`          | EDA OBS plots (output of 06)                                 |
| `12`          | Input layer plots and information                            |
| `13`          | Gaussian vs. No gaussian comparison: map and histogram       |
| `22a` / `22b` | Example segmentation (OBS / ICON), global and zoom on region |
| `43`          | Input layer PDF/CDF                                          |

Exceptions (plots live in the main notebook):
- warm BT mean of deleted cell features = in `25`
- linked and filtered tracks and histograms of linking filter effects = in `53`.

### `nbooks_plotting_2/`

| Nbook | Purpose                                                       |
| ----- | ------------------------------------------------------------- |
| `2`   | Evaluation plots, cores vs. sisters bar plot                  |
| `5`   | Relative slopes                                               |
| `6`   | Absolute slopes with annual means                             |
| `9`   | IWP mean and precipitation mean scatter plot for PE           |
| `10`  | Quick MCS "classification"                                    |
| `11`  | Sensitivity analysis for block bootstrapping input parameters |
| `12`  | Development of tas over time                                  |

### `nbooks_additional/`

Old and experimental notebooks (first tobac attempts, loading/familiarization of CCIC, IMERG, NASA Tb and ICON data, GIFs, cheat sheets). Kept for reference only; deprecated.



## 7. Data sources, citation, contact

- Simulation:
	- ICON *ngc4008* (production run NextGEMS)
		- Segura, H., et al.: nextGEMS: Entering the Era of Kilometer-Scale Earth System Modeling, Geoscientific Model Development, 18, 7735–7761, https://doi.org/10.5194/gmd-18-7735-2025, 2025
- Observations:
	- NCEP/CPC L3 Half Hourly 4km Global (60◦S 60◦N) Merged IR V1  (NASA-Tb)
		- Janowiak, J., Joyce, B., and Xie, P.: NCEP/CPC L3 Half Hourly 4km Global (60S- 60N) Merged IR V1, https://doi.org/10.5067/P4HZB9N27EKU, 2017
	- GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07
		- Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., and Tan, J.: GPM IMERG Final Precipitation L3 Half Hourly 0.1 Degree x 0.1 Degree V07, https://doi.org/10.5067/GPM/IMERG/3B-HH/07, 2023
	- Chalmers Cloud Ice Climatology CPCIR
		- Amell, A., Pfreundschuh, S., and Eriksson, P.: The Chalmers Cloud Ice Climatology: Retrieval Implementation and Validation, Atmospheric Measurement Techniques, 17, 4337–4368, https://doi.org/10.5194/amt-17-4337-2024, 2024
- Tracking:
	- tobac 1.6.3 (Tracking and Object-Based Analysis of Clouds)
		- Heikenfeld, M., Marinescu, P. J., Christensen, M., Watson-Parris, D., Senf, F., van den Heever, S. C., and Stier, P.: Tobac 1.2: Towards a Flexible Framework for Tracking and Analysis of Clouds in Diverse Datasets, Geoscientific Model Development, 12, 4551–4570, https://doi.org/10.5194/gmd-12-4551-2019, 2019
		- Sokolowsky, G. A., Freeman, S. W., Jones, W. K., Kukulies, J., Senf, F., Marinescu, P. J., Heikenfeld, M., Brunner, K. N., Bruning, E. C., Collis, S. M., Jackson, R. C., Leung, G. R., Pfeifer, N., Raut, B. A., Saleeby, S. M., Stier, P., and van den Heever, S. C.: Tobac v1.5: Introducing Fast 3D Tracking, Splits and Mergers, and Other Enhancements for Identifying and Analysing Meteorological Phenomena, Geoscientific Model Development, 17, 5309–5330, https://doi.org/ 10.5194/gmd-17-5309-2024, 2024.
- Contact: Leonie Hartog, leonie.hartog@uni-leipzig.de, leoniehartog@gmx.de