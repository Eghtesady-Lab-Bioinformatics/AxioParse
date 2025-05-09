# :computer: AxioParse: Streamlining Axiom Microbiome Assay data wrangling and dataset generation.

The Applied Biosystems Axiom Microbiome Array is a high throughput tool to detect bacteria, archaea, viruses, protozoa and fungi simultaneously in multiple samples, but Applied Biosystem’s provided software’s functions are highly limited. Researchers interested in analyzing such microbiome data are required to perform complex data wrangling before it is useable in platforms like R or QIIME2. This pre-configured, user-friendly, visual, and easily customizable pipeline allows the user to generate datasets formatted for QIIME, common R packages, and other downstream analysis. 

AxioParse was built in Python as a directed acyclic graph (DAG) using Dagster. Dagster is a modern orchestration framework designed for building, deploying, and managing data workflows with a strong emphasis on modularity, observability, and reproducibility. This format allows users to visualize the pipeline through a locally hosted graphical user interface and make adjustments with minimal Python knowledge. 

## :file_folder: Relevant Repository Contents
- `axioparase_pipeline/assets.py`: Contains all assets for the DAG pipeline
- `axioparse_pipeline/extra_functions.py`: Contains extra functions utilized in assets.py
- `data/otu_table.txt`: Test dataset containing example probes and samples. This sample dataset is in the same format as one directly downloaded from the Axiom MiDAS software.
- `data/metadata.csv`: A sample metadata table.
- `data/array_species_coverage.csv`: A sample species coverage table in the same format as one downloaded directly from MiDAS.

## :beginner: Getting Started

### Setup and Pulling Code
1. Open a terminal window and run `python --version`.
    - If python is not installed or you have a python version lower than 3.9, download the newest python version [here](https://www.python.org/downloads/).
    - If the python version downloaded is greater than 3.9, this step is complete. 
1. Use `cd` commands within the terminal window to navigate into your preferred directory. This location will be where all the code is stored within a folder called "axioparse".
2. Pull the repository contents to your device with the terminal command `git clone https://github.com/Eghtesady-Lab-Bioinformatics/axioparse.git`. This will create a new folder called `axioparse` within your directory.
2. If you're using Windows, you will need to download Windows Subsystem for Linux to continue forward. Follow the instructions [here](https://learn.microsoft.com/en-us/windows/wsl/install). You will need to use the WSL terminal for the remainder of this tutorial, not Windows Command Prompt. If you're on a Mac, you can skip this step.

### Prepare Environment
5. Using a terminal window (WSL terminal if using Windows, default terminal if using Mac) and `cd` commands, enter this project's directory. Follow the instructions [here](https://library.qiime2.org/quickstart) to create a Conda virtual environment for this project and install the QIIME2 package.   
    - Once you click the link, you will need to choose a distribution. I recommend the Tiny Distribution, but any should work.
    - Once you choose a distribution, follow the "Using Conda" instructions. You don't need to complete "Using Docker".
    - As a part of "1. Installing Miniconda", you will need to follow the links to the Miniconda instructions and download that program separately. 
4. Open a new terminal window. Use `cd` commands to navigate into the `AxioParse` directory.
4. Activate the conda environment previously downloaded with `conda activate env_name`. Replace `env_name` with the environment name (for example, if you used the Tiny version, it might be `qiime2-tiny-2025.4`). You can verify that the environment was activated properly by checking at the terminal command line starts with `(env_name)`. 
5. Use the command `pip install .` to install all dependencies into the virtual environment. 

### File Adjustments
9. Use the terminal command below to create a `.env` file in the axioparse directory. This file will store your NCBI email and API key for Entrez access. Instructions to obtain an NCBI Entrez API Key can be found [here](https://support.nlm.nih.gov/kbArticle/?pn=KA-05317). Once this file is created, it will be hidden from view in the file explorer by default.  
```
echo 'NCBI_EMAIL="your.email@domain.com"' >> .env 
echo 'NCBI_KEY="your_ncbi_key_here"' >> .env 
```
7. Use the terminal command `mkdir data_out` to create a folder to contain output data.
8. Use the terminal command `printf "\ndata/\n" >> .gitignore` to add the `data` folder to the gitignore.

### Run Process in Dagster
12. In the same terminal window, run the command `dagster dev`. This should launch Dagster on your local server, which you can access by clicking on [this link](http://127.0.0.1:3000) or the link generated in the terminal window. 
8. Select the "Assets" tab in the top left, and then click "View global asset lineage" in the top right. Execute the pipeline by selecting "Materialize All" in the top right.
9. The output files will be written into `/data_out/`.
10. When finished, navigate back to the terminal window and click `Ctrl + c` to kill the process. 

## :inbox_tray: Input
- `otu_table.txt`: OTU table downloaded directly from MiDAS software
- `metadata.csv`: A metadata table in which each row corresponds to a single sample. Required columns are `sample_id` and `array_id` (matches column headers in `otu_table.csv`). 
- `array_species_coverage.csv`: Phylogeny of all possible probes on the microarray. Each row is a probe, and columsn "Sequence", "Domain", and "Family" are required. Items in "Sequence" must match items in the "Target Description" column of `otu_table.txt`. This spreadsheet is provided by the Axiom group. 

## :outbox_tray: Output
The following files will be written to `/data_out/`
- `metadata_qiime.txt`: Metadata file compatible with [QIIME2](https://qiime2.org/).
- `metadata_r.csv`: Metadata file compatible with the [MicrobiomeStat R package](https://github.com/cafferychen777/MicrobiomeStat)
- `otu_table_qiime.biom`: OTU table in a format ready for [QIIME2](https://qiime2.org/). 
- `otu_table_r.csv`: OTU table compatible with the [MicrobiomeStat R package](https://github.com/cafferychen777/MicrobiomeStat)
- `taxonomy_qiime.txt`: Taxonomy table compatible with [QIIME2](https://qiime2.org/)
- `taxonomy_r.csv`: Taxonomy table compatible with the [MicrobiomeStat R package](https://github.com/cafferychen777/MicrobiomeStat)

## :pencil2: Authors
Pranav Kirti, Eghtesady Lab @ Washington University in St. Louis

The code is open-source under the MIT Lisence. Please cite this github page using the citation feature on the right.

![DAG Pipeline](pictures/pipeline.svg)
