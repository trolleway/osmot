#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time
import config
import argparse


def download_osm():
	import urllib
	urllib.urlretrieve ('''http://overpass.osm.rambler.ru/cgi/interpreter?data=relation["route"="trolleybus"](55.620,37.510,55.91,37.85 );(._;>;);out meta;''', "data.osm")

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('--download', dest='download', action='store_true')
    parser.add_argument('--no-download', dest='download', action='store_false')
    parser.set_defaults(download=True)

    parser.epilog = \
        '''Samples:
%(prog)s --download
%(prog)s --no-download

''' \
        % {'prog': parser.prog}
    return parser




def cleardb(host,dbname,user,password):
        ConnectionString="dbname=" + dbname + " user="+ user + " host=" + host + " password=" + password

	try:

		conn = psycopg2.connect(ConnectionString)
	except:
		print 'I am unable to connect to the database                  ' 
                print ConnectionString
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
	osm2pgsql --create --slim --latlong --database '''+dbname+''' --username '''+user+'''  data.osm
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

        parser = argparser_prepare()
        args = parser.parse_args()

        is_download = args.download
	if is_download == True:
		print "downloading"
        	download_osm()

	cleardb(host,dbname,user,password)
	importdb(host,dbname,user,password)
	process(host,dbname,user,password) 
