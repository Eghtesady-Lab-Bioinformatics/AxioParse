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
1. Pull the repository contents to your device with the command `git clone https://github.com/Eghtesady-Lab-Bioinformatics/axioparse.git`
2. If you're using windows, you will need to download Windows Subsystem for Linux to continue forward. Follow the instructions [here](https://learn.microsoft.com/en-us/windows/wsl/install). If you're on a Mac, you can skip this step.
3. Using a terminal window (WSL terminal if using Windows) and `cd` commands, enter this project's directory. Follow the instructions [here](https://library.qiime2.org/quickstart) to create a Conda virtual environment for this project and install the QIIME2 package. I used the Tiny Distribution, but any should work. 
3. Create a file called .env in the root directory. In the file, write `NCBI_EMAIL = "your.email@domain.com"`. On the next line, write `NCBI_KEY = "ncbi_key_here"`. Instructions to obtain an NCBI Entrez API Key can be found [here](https://support.nlm.nih.gov/kbArticle/?pn=KA-05317).
4. In the terminal window (recall that you should be within the root directory), activate the conda environment with `conda activate <env_name>`. 
3. Once the conda environment is activated, use the command `pip install .` to install all dependencies into the virtual environment. 
5. Make an empty folder  `/data_out/` in the root directory.
6. Inside the .gitignore file, add a new line and type `data/`.
7. In the same terminal window, run the command `dagster dev`. This should launch Dagster on your local server, which you can access by clicking on [this link](http://127.0.0.1:3000) or the link generated in the terminal window. 
8. Execute the pipeline by selecting "Materialize All" in the top right.
9. The output files will be written into `/data_out/`.

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
