#!/usr/bin/env python
from sqlalchemy import create_engine

def get_conn():
    return create_engine('postgresql://postgres:password@0.0.0.0:5432/wxdata')
