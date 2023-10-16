"""
Weather data ingester

This script allows the user to process wx weatehr data, do a little cleanup, then push to a postgres docker container.

Authored by Vivek Bansal
"""
import csv
import glob
from io import StringIO
import logging
from logging.handlers import RotatingFileHandler
import time

import pandas as pd

from utils import get_conn

logger = logging.getLogger('ingestion')
logging.basicConfig(
        handlers=[RotatingFileHandler('./ingestion.log', maxBytes=10000000, backupCount=10)],
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')

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

def read_in_tsvs():

    allFiles = glob.glob('.' + "/wx_data/USC*.txt")
    frames = []
    for file_ in allFiles:
        logging.debug(f"Reading in {file_}")
        frame = pd.read_csv(file_, header=None, sep='\t', na_values='-9999')
        frame['station'] = file_.split('/')[2].split('.')[0] #Get the weather station name
        frames.append(frame)
    df = pd.concat(frames).drop_duplicates(ignore_index=True)
    df = df.rename(columns={0: 'wx_date',1: 'max_temp',2:'min_temp', 3:'precip'}).assign(
        wx_date=lambda x: pd.to_datetime(x['wx_date'], format='%Y%m%d'))
    df['year'] = df.wx_date.dt.year
    return df

def process_stats_df(df):

    precip_df = df.groupby(['station','year'])['precip'].sum().reset_index()

    precip_df['precip'] = precip_df['precip']*.01 #Convert to centimeters of rain (from tenths of a millimeter), 
                                                  #not sure about sig figs

    max_df = df.groupby(['station','year'])['max_temp'].mean().reset_index()
    max_df['max_temp'] = max_df['max_temp'].round()*.1 #Convert to degrees Celcius (from tenths fo a degree Celcius),
                                                       #not sure about sig figs
    min_df = df.groupby(['station','year'])['min_temp'].mean().reset_index()
    min_df['min_temp'] = min_df['min_temp'].round()*.1 #Convert to degrees Celcius, not sure about sig figs

    stats_df = pd.merge(pd.merge(max_df,min_df,how='outer'),precip_df,how='outer')
    stats_df = stats_df.rename(columns={'max_temp':'yearly_max_temp_avg','min_temp': 'yearly_min_temp_avg','precip':'yearly_precip_total'})
    return stats_df

start = time.time()

logging.info("Read in tsvs")
df = read_in_tsvs()

logging.info("Process stats df")
stats_df = process_stats_df(df)
del df['year']

engine = get_conn()

logging.info("Upload/replace stats df")
stats_df.to_sql(
    name="weather_stats",
    con=engine,
    if_exists="replace",
    index=False,
    method=psql_insert_copy
)

# TODO Create optmized tables in postgres.  These are not indexed.
logging.info("Upload/replace weather df")
df.to_sql(
    name="weather_data",
    con=engine,
    if_exists="replace",
    index=False,
    method=psql_insert_copy
)
end = time.time()
logging.info(f"Ingestion processing time: {end - start}")
