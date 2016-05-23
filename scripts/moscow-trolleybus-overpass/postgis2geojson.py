#!/usr/bin/python
# -*- coding: utf8 -*-


import config
import os

def postgis2geojson(host,dbname,user,password,table):
	os.system('''
ogr2ogr -f GeoJSON '''+table+'''.geojson \
  "PG:host='''+host+''' dbname='''+dbname+''' user='''+user+''' password='''+password+'''" "'''+table+'''"
	''')

if __name__ == '__main__':
        host=config.host
        dbname=config.dbname
        user=config.user
        password=config.password


	postgis2geojson(host,dbname,user,password,'terminals_export')
	postgis2geojson(host,dbname,user,password,'routes_with_refs')
