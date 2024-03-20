import pandas as pd
import json
import typing as t
import re
import os

# DATA_PATH = f"/opt/airflow/data/ademe-dpe-tertiaire"
# API_PATH = "/opt/airflow/data/api/"
DATA_PATH = "/Users/alexis/work/ademe_mlops/data/"
URL_FILE = os.path.join(DATA_PATH, "api", "url.json")
RESULTS_FILE = os.path.join(DATA_PATH, "api", "results.json")

from db_utils import Database


def rename_columns(columns: t.List[str]) -> t.List[str]:
    """
    rename columns
    """

    columns = [col.lower() for col in columns]

    rgxs = [
        (r"[°|/|']", "_"),
        (r"²", "2"),
        (r"[(|)]", ""),
        (r"é|è", "e"),
        (r"â", "a"),
        (r"^_", "dpe_"),
        (r"_+", "_"),
    ]
    for rgx in rgxs:
        columns = [re.sub(rgx[0], rgx[1], col) for col in columns]

    return columns


if __name__ == "__main__":
    assert os.path.isfile(RESULTS_FILE)

    # read previous API call output
    with open(RESULTS_FILE, encoding="utf-8") as file:
        data = json.load(file)

    data = pd.DataFrame(data["results"])

    print(f"loaded {data.shape}")

    # set columns
    new_columns = rename_columns(data.columns)
    data.columns = new_columns

    # to_sql
    db = Database()
    data.to_sql(name="dpe_tertiaire", con=db.engine, if_exists="append", index=False)
    db.close()
