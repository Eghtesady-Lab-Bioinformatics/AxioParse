import pandas as pd
from Bio import Phylo
from io import StringIO
import pytest
import qiime2
import biom
import skbio

@pytest.mark.data_in
def test_otus_in_species_cov():
    otu_table = pd.read_csv("./data/otu_table.csv", dtype=str)
    species_cov = pd.read_csv("./data/array_species_coverage.csv")

    all_probes = set(species_cov["Sequence"])
    relevant_otus = set(otu_table["Target Description"])

    assert relevant_otus.issubset(all_probes)