from setuptools import find_packages, setup

setup(
    name="axioparse_pipeline",
    version="0.1.0",
    author="Pranav Kirti",
    packages=find_packages(exclude=["axioparse_pipeline_tests"]),
    python_requires=">=3.9.19",
    install_requires=[
        "dagster~=1.8.1",
        "dagster_duckdb_pandas~=0.24.1",
        "dagster_duckdb~=0.24.1",
        "dagster-cloud~=1.8.1",
        "pandas~=2.2.2",
        "numpy~=1.26.4",
        "biopython~=1.78",
        "python-dotenv~=1.0.1",
        "scikit-bio~=0.6.0",
        "pytest~=8.2.1",
        "dagster-webserver~=1.8.1"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
