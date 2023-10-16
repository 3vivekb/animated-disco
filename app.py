"""
Weather data server

This simple flask api helps users to make queries against a rest api to hit the processed and unprocessed weather data.

Authored by Vivek Bansal
"""

import json

from flask import Flask, request
import pandas as pd

from utils import get_conn

app = Flask(__name__)

def weather_clause_query(date_clause, station_clause, args, stats_table=False):
    """
    Returns: String object
    """
    if stats_table:
        date_col_name = "year"
    else:
        date_col_name = "wx_date"

    if date_clause and station_clause:
        where_clause = f"""WHERE {date_col_name} BETWEEN '{args.get('from_date')}' AND '{args.get('to_date')}'
                        AND station = '{args.get('station')}'
        """
    elif date_clause:
        where_clause = f"""WHERE {date_col_name} BETWEEN '{args.get('from_date')}' AND '{args.get('to_date')}'
        """
    elif station_clause:
        where_clause = f"""WHERE station = '{args.get('station')}'
        """
    else:
        where_clause = ""

    return where_clause


@app.route('/')
def default():
    """
    Returns: Hello World
    """
    return "<p>Hello!</p>"

@app.route('/api/weather', methods=['GET'])
def get_weather_data():
    """
    Returns weather data
    ---
    parameters:
          - page_size: int
            page: int
            from_date: 'YYYY-MM-DD'
            to_date: 'YYYY-MM-DD'
            station: string
    Returns: JSON object
    """
    args = request.args
    date_clause, station_clause = False, False

    if args.get('from_date') and args.get('to_date'):
        date_clause = True

    if args.get('station'):
        station_clause = True

    where_clause = weather_clause_query(date_clause, station_clause, args)
    
    limit_size = 1000
    if args.get('page_size'):
        limit_size = int(args.get('page_size'))
    page = 0
    if args.get('page'):
        page = int(args.get('page'))

    engine = get_conn()
    dbConnection    = engine.connect()
    res = pd.read_sql(f"""
                      select * from weather_data {where_clause} 
                      limit {limit_size + 1}
                       offset {limit_size*page}
                      """, dbConnection)
    if res.shape[0] > limit_size:
        res = res[:-1]
        has_next_page = True
    else:
        has_next_page = False
    res_records = res.to_json(orient='records')
    return {"message": "success", "next_page": has_next_page, "data": json.loads(res_records)}

@app.route('/api/weather/stats', methods=['GET'])
def get_weather_stats():
    """
    Returns weather stats data
    ---
    parameters:
          - page_size: int
            page: int
            from_date: 'YYYY'
            to_date: 'YYYY'
            station: string
    Returns: JSON object
    """    
    args = request.args
    date_clause, station_clause = False, False

    if args.get('from_date') and args.get('to_date'):
        date_clause = True

    if args.get('station'):
        station_clause = True

    where_clause = weather_clause_query(date_clause, station_clause, args, stats_table=True)
    limit_size = 1000
    if args.get('page_size'):
        limit_size = int(args.get('page_size'))
    page = 0
    if args.get('page'):
        page = int(args.get('page'))

    engine = get_conn()
    dbConnection    = engine.connect()
    res = pd.read_sql(f"""
                      select * from weather_stats {where_clause} 
                      limit {limit_size + 1}
                       offset {limit_size*page}
                      """, dbConnection)
    if res.shape[0] > limit_size:
        res = res[:-1]
        has_next_page = True
    else:
        has_next_page = False
    res_records = res.to_json(orient='records')
    return {"message": "success", "next_page": has_next_page, "data": json.loads(res_records)}

if __name__ == '__main__':
    app.run()