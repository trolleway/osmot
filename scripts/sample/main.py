#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time

# Create database tables with map of Kolomna tram

def cleardb():
	dbname='osmot'
	user='user'
	host='localhost'
	password='user'
	try:
		conn = psycopg2.connect("dbname='" + dbname + "' user='"
                                + user + "' host='" + host
                                + "' password='" + password + "'")
	except:
		print 'I am unable to connect to the database'
		return 0
	cur = conn.cursor()
	sql ='''
	DROP TABLE IF EXISTS planet_osm_buildings;
	DROP TABLE IF EXISTS planet_osm_line;
	DROP TABLE IF EXISTS planet_osm_nodes;
	DROP TABLE IF EXISTS planet_osm_point;
	DROP TABLE IF EXISTS planet_osm_polygon;
	DROP TABLE IF EXISTS planet_osm_rels;
	DROP TABLE IF EXISTS planet_osm_roads;
	DROP TABLE IF EXISTS planet_osm_ways;
	DROP TABLE IF EXISTS route_line_labels;
	DROP TABLE IF EXISTS routes_with_refs;
	DROP TABLE IF EXISTS terminals;
	DROP TABLE IF EXISTS terminals_export;	
	'''

	cur.execute(sql)
	conn.commit()

def importdb():
	os.system('''
	osm2pgsql -s -l -C 700 -c -d osmot -U user  kolomna.osm
	''')

def process():
	os.system('''
	python ../../osmot.py -hs localhost -d osmot -u user -p user
	''')




if __name__ == '__main__':
	cleardb()
	importdb()
	process() 
