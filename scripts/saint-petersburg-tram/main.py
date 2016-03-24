#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time
import config
import argparse


def download_osm():
	import urllib
	#urllib.urlretrieve ('''http://overpass.osm.rambler.ru/cgi/interpreter?data=%5Bout%3Axml%5D%5Btimeout%3A25%5D%3B%28relation%5B%22route%22%3D%22tram%22%5D%2859%2E81660471427925%2C30%2E005893707275387%2C59%2E89022865212811%2C30%2E164337158203125%29%3B%29%3Bout%20meta%3B%3E%3Bout%20meta%20qt%3B%0A''', "data.osm")
	urllib.urlretrieve ('''http://overpass.osm.rambler.ru/cgi/interpreter?data=%5Bout%3Axml%5D%5Btimeout%3A25%5D%3B%28relation%5B%22route%22%3D%22tram%22%5D%2859%2E80754134191466%2C30%2E047607421875%2C60%2E098403034443926%2C30%2E595550537109375%29%3B%29%3Bout%20meta%3B%3E%3Bout%20meta%20qt%3B%0A''', "data.osm")
	#http%3A%2F%2Foverpass.osm.rambler.ru%2Fcgi%2Finterpreter%3Fdata%3D%5Bout%3Axml%5D%5Btimeout%3A25%5D%3B(relation%5B%22route%22%3D%22tram%22%5D(29.935%2C59.7398%2C30.6409%2C60.0963)%3B)%3Bout%20meta%3B%3E%3Bout%20meta%20qt%3B
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
	osm2pgsql --create  --slim --database '''+dbname+''' --username '''+user+''' --password --port  5432 --host localhost --style default.style data.osm
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
