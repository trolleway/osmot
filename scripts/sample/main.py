#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time
import config

# Create database tables with map of Kolomna tram

def cleardb(host,dbname,user,password):
        ConnectionString="dbname='" + dbname + "' user='"+ user + "' host='" + host + "' password='" + password + "'"

	try:
		conn = psycopg2.connect(ConnectionString)
	except:
		print 'I am unable to connect to the database'
		return 0
	cur = conn.cursor()
	sql ='''
	DROP TABLE IF EXISTS planet_osm_buildings 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_line 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_nodes 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_point 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_polygon 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_rels 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_roads 		CASCADE;
	DROP TABLE IF EXISTS planet_osm_ways 		CASCADE;
	DROP TABLE IF EXISTS route_line_labels 		CASCADE;
	DROP TABLE IF EXISTS routes_with_refs 		CASCADE;
	DROP TABLE IF EXISTS terminals 			CASCADE;
	DROP TABLE IF EXISTS terminals_export 		CASCADE;
	'''

	cur.execute(sql)
	conn.commit()

def importdb(host,dbname,user,password):
	os.system('''
	osm2pgsql -s -l -C 700 -c -d '''+dbname+''' -U '''+user+'''  kolomna.osm
	''')

def process(host,dbname,user,password):
	
        cmd='''python ../../osmot.py -hs localhost -d '''+dbname+''' -u '''+user+''' -p '''+password+'''
	'''
        print cmd
        os.system(cmd)




if __name__ == '__main__':
        host=config.host
        dbname=config.dbname
        user=config.user
        password=config.password

	cleardb(host,dbname,user,password)
	importdb(host,dbname,user,password)
	process(host,dbname,user,password) 
