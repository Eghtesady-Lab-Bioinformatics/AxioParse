from dagster import asset
import os
import pandas as pd
import numpy as np
from . import extra_functions
from biom import Table
import json
import io
from dagster import asset
from Bio import Entrez
import time
import re
from dotenv import load_dotenv
import warnings

# ASSIGN GLOBAL VARIABLES
load_dotenv()
Entrez.email = os.getenv("NCBI_EMAIL")
Entrez.api_key = os.getenv("NCBI_KEY")
OTU_IN_PATH = './data/otu_table.txt'
METADATA_IN_PATH = './data/metadata.csv'
SPEC_COV_IN_PATH = './data/array_species_coverage.csv'

### ASSETS TO READ IN THE DATA AND PREP FOLDERS
@asset(group_name="read_data")
def read_otu():
    '''
    Step R.2: upload the otu table as a dataframe, do some formatting
    '''
    otu_table = pd.read_csv(OTU_IN_PATH, sep='\t')
    otu_table.sort_values(by="Target Description", inplace=True)
    otu_table.rename(columns={"Target Description":"Probe"}, inplace=True)
    return otu_table

@asset(group_name="read_data")
def read_metadata():
    '''
    Step R.1: upload the metadata file as a dataframe
    '''
    metadata = pd.read_csv(METADATA_IN_PATH)
    return metadata

@asset(group_name="read_data")
def read_species_coverage():
    '''
    Step R.3: upload the species coverage file as a dataframe, do some formatting
    '''
    specices_cov = pd.read_csv(SPEC_COV_IN_PATH)
    specices_cov.rename(columns={"Sequence":"Probe"}, inplace=True)
    return specices_cov


#### ASSETS TO CLEAN THE OTU TABLE
@asset(group_name="clean_otu_table")
def replace_sample_names(read_otu, read_metadata):
    '''
    Step O.1: replace column headers in otu table with sample_id from metadata
    '''
    id_mapping = dict(zip(read_metadata['array_id'], read_metadata['sample_id']))
    read_otu.rename(columns=id_mapping, inplace=True)
    return read_otu

@asset(group_name="clean_otu_table")
def merge_samples_to_otu(replace_sample_names, read_species_coverage):
    '''
    Step O.2: merge the species column from species coverage onto the otu table
    '''
    merged = replace_sample_names.merge(read_species_coverage[['Probe', 'Species']], on='Probe', how='left')

    # reorder columns to put species first
    cols = ['Species'] + [col for col in merged.columns if col != 'Species']
    merged = merged[cols]

    # sort rows by Species name
    merged.sort_values(by=['Species', 'Probe'], inplace=True)

    return merged

@asset(group_name="clean_otu_table")
def replace_species_names(merge_samples_to_otu, enrich_taxonomy_table):
    '''
    Step O.3: Replace species names using updated taxonomy information
    '''
    otu_table = merge_samples_to_otu
    otu_table = otu_table.rename(columns={"Species": "Old Species"})

    # create mapping dictionary
    mapping = dict(zip(enrich_taxonomy_table["Original Species"], enrich_taxonomy_table["Species"]))
    otu_table["Species"] = otu_table["Old Species"].map(mapping)

    # throw error if mapping isn't complete
    if otu_table["Species"].isnull().any():
        unmatched = otu_table.loc[otu_table['Species'].isnull(), "Old Species"].tolist()
        raise ValueError(f"The following species values could not be matched in replace_species_names: {unmatched}. Check that all species are searched properly when Taxonomy API is searched")
    
    # reorganize the columns in otu table to have species first
    otu_table = otu_table.drop(columns=["Old Species", "Probe"])
    cols = ["Species"] + [col for col in otu_table.columns if col != "Species"]

    # re-sort the columns by species so that remove_duplicates works
    otu_table = otu_table[cols].sort_values(by="Species")

    return otu_table


@asset(group_name="clean_otu_table")
def remove_duplicates(replace_species_names):
    '''
    Step O.4: aggregates data for duplicate species and then empties and deletes duplicate rows.
    Note: aggregates into DETECTED or Secondary. user can add print statement at the end of this function to output
    a table aggregated based on species but with all original columns. 
    '''

    for i in range(0, len(replace_species_names)-1):
        if replace_species_names.iloc[i,0] == replace_species_names.iloc[i+1,0]:
            for j in range(2, len(replace_species_names.iloc[0,:])):
                test_if = False

                if pd.isna(replace_species_names.iloc[i,j]) and pd.isna(replace_species_names.iloc[i+1,j]):
                    test_if=True
                
                elif ((replace_species_names.iloc[i, j] == "Secondary") and (replace_species_names.iloc[i + 1, j] == "Secondary")) or \
                     ((replace_species_names.iloc[i, j] == "Secondary") and (pd.isna(replace_species_names.iloc[i + 1, j]))) or \
                     ((pd.isna(replace_species_names.iloc[i, j])) and (replace_species_names.iloc[i + 1, j] == "Secondary")):
                    replace_species_names.iloc[i+1, j] = "Secondary"
                    test_if = True
                
                elif (replace_species_names.iloc[i, j] == "DETECTED") or (replace_species_names.iloc[i+1, j] == "DETECTED"):
                    replace_species_names.iloc[i+1, j] = "DETECTED"
                    test_if = True

                else:
                    raise ValueError(f"ERROR: Lines not condensed at row {i} and column {j}")
                
            if test_if:
                for j in range(0, len(replace_species_names.iloc[0,:])):
                    replace_species_names.iloc[i, j] = np.nan
    
    replace_species_names.dropna(subset=[replace_species_names.columns[0]], axis=0, inplace=True)

    return replace_species_names

@asset(group_name="clean_otu_table")
def combine_dna_rna_probes(remove_duplicates):
    '''
    Step O.5: combines all dna and rna probes and makes all dna values binary
    '''
    result_df = remove_duplicates.apply(extra_functions.aggregate_row_to_binary, axis=1, result_type='expand')

    return result_df

@asset(group_name="clean_otu_table")
def delete_extra_samples(combine_dna_rna_probes, read_metadata):
    '''
    Step O.6: deletes all columns where the axiom id was not replaced with a sample id (the sample does not have
    corresponding metadata)
    '''
    sample_ids = set(read_metadata["sample_id"])
    filtered_list = [item for item in combine_dna_rna_probes.columns if ((item in sample_ids) or (item == "Species"))]
    
    return combine_dna_rna_probes[filtered_list]

@asset(group_name="clean_otu_table")
def cut_probe_names(delete_extra_samples):
    '''
    Step O.7: delete probe names from otu table
    '''
    delete_extra_samples.sort_values(by="Species", inplace=True)
    delete_extra_samples.drop(columns=['Species'], inplace=True)
    delete_extra_samples.reset_index(drop=True, inplace=True)

    return delete_extra_samples


# ASSETS TO PREPARE THE TAXONOMY TABLE
@asset(group_name="clean_tax_table")
def filter_taxa(read_species_coverage, merge_samples_to_otu):
    '''
    Step T.1: filter the taxonomy table to include phylogeny information on otus in the otu table. do some extra
    formatting.
    '''

    species_cov = read_species_coverage[read_species_coverage['Species'].isin(merge_samples_to_otu['Species'])]
    tax_table = species_cov[["Domain", "Family", "Species"]]
    tax_table.drop_duplicates(subset=['Species'], inplace=True)
    tax_table.sort_values(by="Species", inplace=True) 
    tax_table.reset_index(drop=True, inplace=True)

    return tax_table

@asset(group_name="clean_tax_table")
def enrich_taxonomy_table(read_species_coverage, filter_taxa):
    """
    Step T.2: For each Species in tax_table, search the NCBI Taxonomy database to get full taxonomic info.
    If not found, attempt probe-based fallback search. Raise error if any entries fail.
    """

    failed_species = []
    taxonomy_rows = []
    tax_table = filter_taxa

    # throw an error if api email and key aren't loaded in
    extra_functions.validate_api()

    for _, row in tax_table.iterrows():
        original_species = row['Species']

        # do initial search with species
        tax_id_list = extra_functions.search_ncbi_taxonomy(original_species)
        tax_id_list = [tid for tid in tax_id_list if tid.strip().isdigit()]

        # attempt fallback search using probe name if tax_id_list is empty or too long
        if (not tax_id_list) or (len(tax_id_list) > 5):
            matching_probe_row = read_species_coverage[read_species_coverage["Species"] == original_species]
            probe_name = matching_probe_row.iloc[0]['Probe']
            print(f"using fallback search for Original Species: {original_species} and Probe: {probe_name}")
            tax_id_list = extra_functions.fallback_search(probe_name)
            tax_id_list = [tid for tid in tax_id_list if tid.strip().isdigit()]

        # if original and fallback searches failed, append to failed list
        if not tax_id_list:
            warnings.warn(f"skipping rest of loop because {original_species} failed search at checkpoint 1")
            failed_species.append(original_species)
            continue

        # take the first match and collect the taxonomy data for that taxa id. if this fails, append to failed list
        best_tax_id = tax_id_list[0]
        taxonomy_info = extra_functions.fetch_taxonomy_data(best_tax_id, original_species, 3)
        if not taxonomy_info:
            warnings.warn(f"skipping rest of loop because {original_species} failed search at checkpoint 2. returned taxonomy info is {taxonomy_info}")
            failed_species.append(original_species)
            continue
            
        # grab domain from species coverage spreadsheet because NCBI doesn't have it
        domain = re.sub(r'(_noFamily|Families)$', '', row["Domain"])

        # extract lineage info into a dictionary, add that to taxonomy_rows
        lineage = {d['Rank']: d['ScientificName'] for d in taxonomy_info.get('LineageEx', [])}
        lineage.update({'Domain': str(domain),
                        'Kingdom': str(lineage.get('kingdom', '')),
                        'Phylum': str(lineage.get('phylum', '')),
                        'Class': str(lineage.get('class', '')),
                        'Order': str(lineage.get('order', '')),
                        'Family': str(lineage.get('family', '')),
                        'Genus': str(lineage.get('genus', '')),
                        'Species': str(taxonomy_info.get('ScientificName', '')),
                        'Original Species': str(original_species)
        })
        taxonomy_rows.append(lineage)

    if failed_species:
        raise ValueError(f"Failed to find taxonomy for the following species:\n{failed_species}")

    # construct pandas dataframe from taxonomy_rows
    tax_df = pd.DataFrame(taxonomy_rows)[['Domain', 'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species', 'Original Species']]

    return tax_df

@asset(group_name="clean_tax_table")
def remove_duplicate_species(enrich_taxonomy_table):
    '''
    Step T.3: Remove any duplicate species names added while searching the taxonomy table. If there are any duplicates,
    ensure Original Species column contains all the original species for the new one.
    '''

    enrich_taxonomy_table.sort_values(by="Species", inplace=True)
    agg_og = enrich_taxonomy_table.groupby("Species", as_index=False).agg({"Original Species": lambda x: ", ".join(sorted(set(x)))})
    drop_dups = enrich_taxonomy_table.drop_duplicates(subset="Species", keep="first").drop(columns=["Original Species"])
    final_df = pd.merge(agg_og, drop_dups, on="Species").sort_values(by="Species", inplace=False)

    # re-order the columns to put species at the end
    cols = ['Domain', 'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species', 'Original Species']
    
    return final_df[cols]

@asset(group_name="clean_tax_table")
def format_tax_for_qiime(remove_duplicate_species):
    '''
    Step T.4: Reformat taxonomy data into a single column that can be added to otu table
    '''
    remove_duplicate_species.sort_values(by="Species", inplace=True)
    remove_duplicate_species["Full Taxonomy"] = remove_duplicate_species.apply(
        lambda row: f'd_{row["Domain"]}; k_{row["Kingdom"]}; p_{row["Phylum"]}; c_{row["Class"]}; o_{row["Order"]}; f_{row["Family"]}; g_{row["Genus"]}; s_{row["Species"]}', axis=1)
    remove_duplicate_species.reset_index(drop=True, inplace=True)
    remove_duplicate_species.rename(columns={"Species":"Feature ID", "Full Taxonomy":"Taxon"}, inplace=True)
    remove_duplicate_species.drop(columns=["Domain", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Original Species"], inplace=True)

    return remove_duplicate_species

@asset(group_name="clean_otu_table")
def format_ids_for_qiime(delete_extra_samples):

    '''
    Step O.6: manage any special characters present in species names to ensure QIIME2 can handle them 
    '''
    delete_extra_samples.reset_index(drop=True, inplace=True)
    delete_extra_samples.sort_values(by="Species", inplace=True)
    delete_extra_samples.rename(columns={"Species":"#OTU ID"}, inplace=True)
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.replace(' ', '_')
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.replace(r'[\(\)\[\]:]', '*', regex=True)
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.replace('*_', '_')
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.replace('*', '_')
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.rstrip('_')
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.lstrip('_')
    delete_extra_samples['#OTU ID'] = delete_extra_samples['#OTU ID'].str.replace('_', ' ')

    delete_extra_samples.set_index('#OTU ID', inplace=True)

    return delete_extra_samples

# ASSETS TO WRITE FILES FOR QIIME2 AND R
@asset(group_name="write_data")
def write_metadata_r(read_metadata):
    '''
    Step W.2: write metadata into a CSV so that it is useable in the microbiomestat package of R
    '''
    read_metadata.set_index('sample_id', inplace=True)
    read_metadata.index.name = None
    read_metadata.to_csv('./data_out/metadata_r.csv')

@asset(group_name="write_data")
def write_metadata_qiime(read_metadata):
    '''
    Step W.1: write metadata into a .txt as TSV so that it is useable in qiime2
    '''
    type_mapping = {'object': 'categorical', 'bool': 'categorical', 'int64': 'numeric', 'float64': 'numeric'}
    new_row = pd.DataFrame([["#q2:types"] + 
                            [type_mapping.get(str(dtype), 'categorical') 
                             for dtype in read_metadata.dtypes[1:]]], columns=read_metadata.columns)
    
    read_metadata = pd.concat([new_row, read_metadata], ignore_index=True)
    read_metadata.rename(columns={'sample_id':'sample-id'}, inplace=True)

    read_metadata.to_csv('./data_out/metadata_qiime.txt', sep='\t', index=False)

@asset(group_name="write_data")
def write_otu_r(cut_probe_names):
    '''
    Step W.4: write otu table into a csv for r and microbiomestat compatibility
    '''
    cut_probe_names.to_csv('./data_out/otu_table_r.csv')

@asset(group_name="write_data")
def write_otu_qiime(format_ids_for_qiime):
    '''
    Step W.3: write otu table into biom format
    '''
    format_ids_for_qiime.index = format_ids_for_qiime.index.str.replace(" ", "_")
    format_ids_for_qiime.columns = format_ids_for_qiime.columns.str.replace(" ", "_")

    biom_table = Table(format_ids_for_qiime.values, format_ids_for_qiime.index, format_ids_for_qiime.columns)
    biom_json = biom_table.to_json(generated_by="axioparse", direct_io=False)
    with open("./data_out/otu_table_qiime.biom", "w") as biom_file:
        json.dump(json.loads(biom_json), biom_file, indent=4)

@asset(group_name="write_data")
def write_taxonomy_r(remove_duplicate_species):
    '''
    Step W.6: write the taxonomy table to a csv compatible with r and microbiomestat
    '''
    remove_duplicate_species.to_csv('./data_out/taxonomy_r.csv', index=False)


@asset(group_name="write_data")
def write_taxonomy_qiime(format_tax_for_qiime):
    '''
    Step W.5: write taxonomy table to .txt for qiime compatibility
    '''

    format_tax_for_qiime.to_csv('./data_out/taxonomy_qiime.txt', sep='\t', index = False)
