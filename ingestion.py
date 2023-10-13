import csv
import glob
from io import StringIO
import time

import pandas as pd
from sqlalchemy import create_engine

from utils import get_conn

def psql_insert_copy(table, conn, keys, data_iter):
    """

    Execute SQL statement inserting data
    https://pandas.pydata.org/docs/user_guide/io.html#io-sql-method
    https://ellisvalentiner.com/post/a-fast-method-to-insert-a-pandas-dataframe-into-postgres/

    Parameters
    ----------
    table : pandas.io.sql.SQLTable
    conn : sqlalchemy.engine.Engine or sqlalchemy.engine.Connection
    keys : list of str
        Column names
    data_iter : Iterable that iterates the values to be inserted
    """
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)


engine = get_conn()

start = time.time()

allFiles = glob.glob('.' + "/wx_data/USC*.txt")
frames = []
for file_ in allFiles:
    frame = pd.read_csv(file_, header=None, sep='\t', na_values='-9999')
    frame['station'] = file_.split('/')[2].split('.')[0] #Get the weather station name
    frames.append(frame)
df = pd.concat(frames).drop_duplicates(ignore_index=True)
df = df.rename(columns={0: 'wx_date',1: 'max_temp',2:'min_temp', 3:'precip'}).assign(
    wx_date=lambda x: pd.to_datetime(x['wx_date'], format='%Y%m%d'))
df['year'] = df.wx_date.dt.year

precip_df = df.groupby(['station','year'])['precip'].sum().reset_index()
max_df = df.groupby(['station','year'])['max_temp'].mean().reset_index()
max_df['max_temp'] = max_df['max_temp'].round()*.1

min_df = df.groupby(['station','year'])['min_temp'].mean().reset_index()
min_df['min_temp'] = min_df['min_temp'].round()*.1

stats_df = pd.merge(pd.merge(max_df,min_df,how='outer'),precip_df,how='outer')

stats_df.to_sql(
    name="weather_stats",
    con=engine,
    if_exists="replace",
    index=False,
    method=psql_insert_copy
)

del df['year']

df.to_sql(
    name="weather_data",
    con=engine,
    if_exists="replace",
    index=False,
    method=psql_insert_copy
)
end = time.time()
print(end - start)
