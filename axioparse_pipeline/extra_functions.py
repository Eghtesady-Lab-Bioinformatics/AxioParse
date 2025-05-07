import pandas as pd
from Bio import Entrez
from dotenv import load_dotenv
import os
import time
import warnings

load_dotenv()
Entrez.email = os.getenv("NCBI_EMAIL")
Entrez.api_key = os.getenv("NCBI_KEY")

def validate_api():
    if not Entrez.email or not Entrez.api_key:
        raise EnvironmentError("NCBI_EMAIL and/or NCBI_KEY not found in environment variables. We strongly recommend using one before you continue.")
    else:
        print(f"Entrez email = {Entrez.email}")
        print(f"Entrez api_key = {Entrez.api_key}")

def aggregate_row_to_binary(row):
    num_samples = int((len(row)-1)/2)
    for i in range(1, num_samples+1):
        if not pd.isna(row.iloc[i]) or not pd.isna(row.iloc[i + num_samples]):
            row.iloc[i] = 1
        else:
            row.iloc[i] = 0

    return row

def search_ncbi_taxonomy(term):
    try:
        handle = Entrez.esearch(db="taxonomy", term=term)
        record = Entrez.read(handle)
        handle.close()
        time.sleep(0.1)
        return record['IdList']
    except:
        return []

def select_best_tax_id(tax_id_list, search_name):

    handle = Entrez.efetch(db="taxonomy", id=",".join(tax_id_list))
    records = Entrez.read(handle)
    handle.close()
    time.sleep(0.1)

    for record in records:
        if record.get('ScientificName', '').lower() == search_name.lower():
            return record['TaxId']

    return tax_id_list[0]

def fetch_taxonomy_data(tax_id, original_species, retry):
    for attempt_num in range(retry):
        try:
            handle = Entrez.efetch(db="taxonomy", id=tax_id)
            record = Entrez.read(handle)
            handle.close()
            time.sleep(0.1)
            return record[0] if record else None
        except Exception as e:
            time.sleep(0.1 * (attempt_num + 1))
            warnings.warn(f"Attempt {attempt_num + 1} of {retry} failed for original species {original_species} and tax id {tax_id}: {e}")

    warnings.warn(f"All {retry} attempts failed for original species {original_species} and tax id {tax_id}")
    return None
            

def fallback_search(probe_name):
    if probe_name.endswith(", combined chrs"):
        probe_name = probe_name.replace(", combined chrs", "")

    ids = search_ncbi_taxonomy(probe_name)

    if not ids:
        query_parts = probe_name.split()
        while query_parts and not ids:
            probe_query = " ".join(query_parts)
            ids = search_ncbi_taxonomy(probe_query)
            query_parts = query_parts[:-1]
    
    return ids
