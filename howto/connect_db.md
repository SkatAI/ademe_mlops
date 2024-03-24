# connect
```shell
psql --host=<database_name>.postgres.database.azure.com \
    --port=5432 \
    --dbname=database_name \
    --username=<your username> \
    --set=sslmode=require
```


```python
pip install psycopg2-binary

import psycopg2
connection = psycopg2.connect(
    host="<database_name>.postgres.database.azure.com",
    dbname="<database_name>",
    user="<user_name>",
    password="<....>",
    sslmode="require"
)
```

# pandas

gtr.to_sql(name="groundtruth", con=db.engine, if_exists="append", index=False)