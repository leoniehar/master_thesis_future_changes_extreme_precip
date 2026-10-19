# Future Changes of Extreme Tropical Precipitation Cells and their Anvils from a Global Storm-Resolving Simulation

> **Leonie Marie Hartog - University of Leipzig Institute of Meteorology / Leibniz Institute for Tropospheric Research - 2026**

This repository contains the code used to create the material of the Master's thesis.  A publication on Zenodo [https://doi.org/10.5281/zenodo.23436287](https://doi.org/10.5281/zenodo.23436287) contains the related output data needed to reproduce the plots (2a.) as well as the material of this repository. 
## 1. Contents

| Folder               | Content                                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `nbooks/`            | Data processing notebooks (see 4.)                                                                                           |
| `nbooks_additional/` | Old, experimental and deprecated notebooks (not needed to reproduce the thesis)                                              |
| `nbooks_plotting/`   | Plots based on output data  (see 4.)                                                                                         |
| `runner/`            | Shell scripts for parallelization                                                                                            |
| `runner_scripts/`    | Python scripts (converted automatically from the notebooks by the starter) and lists of timestamps etc. used as runner input |
| `starters/`          | Bash wrapper scripts: convert a notebook to a script, make it executable and submit the runner to SLURM                      |
| `tools/`             | Modules used throughout the analysis                                                                                         |
## 2a. How to reproduce the plots
- plotting is done in the notebooks in `nbooks_plotting` based on output data (either recreate it following 2b. or download it from  [10.5281/zenodo.23436287](10.5281/zenodo.23436287))
	- Exceptions (plots live in the main notebook):
		- warm BT mean of deleted cell features = in `25`
		- linked and filtered tracks and histograms of linking filter effects = in `53`.
- set up:
	- environment: use `environment.yaml`, but a standard environment with matplotlib, pandas, xarray, seaborn should also work
	- tools in `/tools`
	- data: use output data from zenodo
		- see`nbooks_plotting` table below
	- for all code that loads/ plots ICON or observational datasets:
		- IMERG reference grid:
			- run **`04`** (save IMERG grid as reference) once.
		- External datasets: accessed via tools `handle_ICON_data`, `handle_OBS_data`
			- ICON *ngc4008* (production run NextGEMS) (Segura et al. 2025)
			- NCEP/CPC L3 Half Hourly 4km Global (60S 60N) Merged IR V1 (NASA-Tb) (Janowiak et al. 2017)
			- GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07 (Huffman et al. 2023)
			- Chalmers Cloud Ice Climatology CPCIR (Amell et al. 2024)
		- NASA Earthdata account:
			- See [https://github.com/nasa/gesdisc-tutorials/blob/main/notebooks/How_to_Generate_Earthdata_Prerequisite_Files.ipynb](https://github.com/nasa/gesdisc-tutorials/blob/main/notebooks/How_to_Generate_Earthdata_Prerequisite_Files.ipynb)
- adapt input paths in notebooks and run
## 2b. How to reproduce the data
- set up:
	- see 2a. for environment, tools & all code that loads/ plots ICON or observational datasets 
	- HPC with SLURM: The starters submit jobs via `sbatch`.
	- code in `nbooks`, executed with runner concept (see 3.)
- used for:
	- **Input field**
		1. Exploratory data analysis `06`  (= `EDA_OBS`)
		2.  Input field comparison `42`  ( =`cdf`)
	- **Monthly datasets (June & December 2023, ICON and OBS)**
		1. Segmentation: `27` (OBS), `28` (ICON), each run with timestamp lists for June and December (=`apply_seg`)
		2. Linking: `51` (executed separately per monthly dataset) (=`linking`)
		3. Filtering: `53` (one run for all four monthly datasets) (=`linking`)
		4. Cell properties / final datasets: `60`
			- saved to `output/final_dataframes/`  (in `final_dataframes`)
		- additional 
			- Characterization of the dataset/ rain amount: `55` (ICON), `56` (OBS), `57` (compile outputs of 56) (used in `54`) (=`aux`)
	- **ICON full (30 years)**
		1. Segmentation: `29`
		2. Add near-surface temperature (tas): `50`
		3. Linking & filtering: `58`
		4. Cell properties / final datasets: `62`
			- saved to `output/final_dataframes/FULL` (in `final_dataframes`)
		5. Annual means (`70`), and slopes (`71`) 
			- saved to `output/annual/` (=`annual`)
## 3. Running notebooks as runners
- overview 
	- `runner/` = Shell scripts for parallelization
	- `runner_scripts/` = Python scripts (converted automatically from the notebooks by the starter) and lists of timestamps etc. used as runner input
	- `starters/` = Bash wrapper scripts: convert a notebook to a script, make it executable and submit the runner to SLURM
- workflow
	1. A **starter** (`starters/`) converts the notebook to a Python script, saves it in `runner_scripts/`, makes it executable and submits the matching **runner** (`runner/`) to SLURM.
		- when reproducing: adapt the environment in the runner!
	2. The runner processes the timestamps from the lists in `runner_scripts/` in parallel (e.g. `timestamps_june.lst`, `timestamps_december.lst`).

```bash
# example 
bash starters/convert_run_nbook27.sh
```

## 4. Notebook overview

**Notebook numbering:** `0x` = data access/preparation, `2x` = segmentation, `4x` = input field comparison, `5x` = linking, rain amount, filtering, `6x` = final datasets, `7x` = change assessment, `8x`= Plotting of evaluation, change assessment, and additional discussion plots
### `nbooks_plotting/`

| Nbook         | Purpose                                                                  | Output data required                       |
| ------------- | ------------------------------------------------------------------------ | ------------------------------------------ |
| `07`          | EDA OBS plots (output of 06)                                             | `EDA_OBS` and IMERG/ Nasa-Tb/ CCIC         |
| `12`          | Input field plots and information                                        | IMERG/ Nasa-Tb/ CCIC                       |
| `13`          | Gaussian vs. No gaussian comparison: map and histogram                   | Nasa-Tb/ CCIC                              |
| `22a` / `22b` | Example segmentation (OBS / ICON), global and zoom on region             | `apply_seg` IMERG/ Nasa-Tb/ CCIC           |
| `43`          | Input field PDF/CDF                                                      | `cdf`                                      |
| `54`          | Explore what the monthly datasets represent (needs data from 55, 56, 57) | `aux`                                      |
| `72`          | Sensitivity analysis for block bootstrapping input parameters            | `final_dataframes` or `annual/sensitivity` |
| `73`          | Development of tas over time                                             | `annual`                                   |
| `80`          | Evaluation plots, cores vs. sisters bar plot                             | `final_dataframes`                         |
| `81`          | Relative slopes                                                          | `annual`                                   |
| `82`          | Absolute slopes with annual means                                        | `annual`                                   |
| `83`          | IWP mean and precipitation mean scatter plot for PE                      | `final_dataframes`                         |
| `84`          | Quick MCS "classification"                                               | `final_dataframes`                         |

### `nbooks/`

| Nbook               | Purpose                                                                                              | Runner | Related dataset / thesis step    |
| ------------------- | ---------------------------------------------------------------------------------------------------- | ------ | -------------------------------- |
| `04`                | Save IMERG grid as reference                                                                         | no     | Prerequisite for all OBS loading |
| `06`                | Count missing timestamps per pixel                                                                   | 06     | exploratory data analysis OBS    |
| `23_interactive`    | OBS segmentation workflow incl. PE                                                                   | no     | Segmentation OBS (development)   |
| `23_inputparameter` | OBS segmentation workflow used for input parameter selection (no PE, no warm BT feature exploration) | 23     | Input parameter selection OBS    |
| `25_interactive`    | ICON segmentation workflow incl. PE                                                                  | no     | Segmentation ICON (development)  |
| `25_inputparameter` | ICON segmentation workflow used for input parameter selection (no PE)                                | 25     | Input parameter selection ICON   |
| `27`                | Apply OBS segmentation workflow                                                                      | 27     | June & December OBS (final)      |
| `28`                | Apply ICON segmentation workflow                                                                     | 28     | June & December  ICON (final)    |
| `29`                | Apply ICON segmentation workflow                                                                     | 29     | ICON full, 30 years (final)      |
| `42`                | PDF and CDF calculation for input field comparison                                                   | 42     | Input field comparison           |
| `50`                | Add tas to ICON full                                                                                 | 50     | ICON full                        |
| `51`                | Link cell features                                                                                   | no     | June & December ICON / OBS       |
| `53`                | Filter tracks                                                                                        | no     | June & December ICON / OBS       |
| `55`                | Rain amount from ICON input fields                                                                   | no     | June & December (ICON)           |
| `56`                | Rain amount from OBS input fields                                                                    | 56     | June & December  (OBS)           |
| `57`                | Compile outputs of 56                                                                                | no     | June & December  (OBS)           |
| `58`                | Link features & filter tracks (equivalent of 51 + 53)                                                | 58     | ICON full                        |
| `60`                | Create final datasets, property calculation                                                          | no     | June & December ICON / OBS       |
| `62`                | Create final datasets, property calculation                                                          | 62     | ICON full                        |
| `70`                | Bootstrapped annual means                                                                            | no     | Change assessment ICON full      |
| `71`                | Slope calculation (based on bootstrap samples from 70)                                               | no     | Change assessment ICON full      |
## 5. Tools Overview
| tools              | Purpose                                                                  |
| ------------------ | ------------------------------------------------------------------------ |
| `cell_props`       | calculation of cell properties                                           |
| `defs_application` | meta data, labels, colors definitions                                    |
| `handle_ICON_data` | loading and handling ICON simulation data                                |
| `handle_OBS_data`  | loading and handling OBS data (Nasa-Tb, IMERG and CCIC)                  |
| `inputlayer`       | functions for PDF/CDF of input field comparisons (calculation and plots) |
| `plots_figures`    | plotting figures                                                         |
| `plots_mapping`    | plotting maps                                                            |
| `use_tobac`        | using tobac                                                              |
## 6. Data sources, contact

- Simulation:
	- ICON *ngc4008* (production run NextGEMS)
		- Segura, H., et al.: nextGEMS: Entering the Era of Kilometer-Scale Earth System Modeling, Geoscientific Model Development, 18, 7735–7761, https://doi.org/10.5194/gmd-18-7735-2025, 2025
- Observations:
	- NCEP/CPC L3 Half Hourly 4km Global (60°S 60°N) Merged IR V1  (NASA-Tb)
		- Janowiak, J., Joyce, B., and Xie, P.: NCEP/CPC L3 Half Hourly 4km Global (60S-60N) Merged IR V1, NASA Goddard Earth Sciences Data and Information Services Center, Greenbelt, MD, https://doi.org/10.5067/P4HZB9N27EKU, 2017.
	- GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07
		- Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., and Tan, J.: GPM IMERG Final Precipitation L3 Half Hourly 0.1 Degree x 0.1 Degree V07, Goddard Earth Sciences Data and Information Services Center (GES DISC), Greenbelt, MD, https://doi.org/10.5067/GPM/IMERG/3B-HH/07, 2023
	- Chalmers Cloud Ice Climatology CPCIR
		- Amell, A., Pfreundschuh, S., and Eriksson, P.: The Chalmers Cloud Ice Climatology: Retrieval Implementation and Validation, Atmospheric Measurement Techniques, 17, 4337–4368, https://doi.org/10.5194/amt-17-4337-2024, 2024
- Tracking:
	- tobac 1.6.3 (Tracking and Object-Based Analysis of Clouds)
		- Heikenfeld, M., Marinescu, P. J., Christensen, M., Watson-Parris, D., Senf, F., van den Heever, S. C., and Stier, P.: Tobac 1.2: Towards a Flexible Framework for Tracking and Analysis of Clouds in Diverse Datasets, Geoscientific Model Development, 12, 4551–4570, https://doi.org/10.5194/gmd-12-4551-2019, 2019
		- Sokolowsky, G. A., Freeman, S. W., Jones, W. K., Kukulies, J., Senf, F., Marinescu, P. J., Heikenfeld, M., Brunner, K. N., Bruning, E. C., Collis, S. M., Jackson, R. C., Leung, G. R., Pfeifer, N., Raut, B. A., Saleeby, S. M., Stier, P., and van den Heever, S. C.: Tobac v1.5: Introducing Fast 3D Tracking, Splits and Mergers, and Other Enhancements for Identifying and Analysing Meteorological Phenomena, Geoscientific Model Development, 17, 5309–5330, https://doi.org/10.5194/gmd-17-5309-2024, 2024.
		
- Contact: Leonie Hartog, leonie.hartog@uni-leipzig.de, le.niehart.g@gmail.com