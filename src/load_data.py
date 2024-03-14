"""
load the data
"""

import csv
import pandas as pd

URL = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-tertiaire-2/lines?size=10000&format=csv&after=10000%2C965634&header=true"

data = pd.read_csv(URL)

assert len(data) > 0

print(data.shape)

OUTPUT_FILE = "./data/dpe_tertiaire_20240314.csv"

data.to_csv(OUTPUT_FILE, index=False, quoting=csv.QUOTE_ALL)
