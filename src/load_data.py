import pandas as pd

url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-tertiaire-2/lines?size=10000&format=csv&after=10000%2C965634&header=true"

data = pd.read_csv(url)

assert len(data) > 0

print(data.shape)

output_file = f"./data/dpe_tertiaire_20240314.csv"
import csv
data.to_csv(output_file, index=False, quoting= csv.QUOTE_ALL)


