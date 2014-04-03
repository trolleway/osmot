#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time
import urllib




def download_osm():
	import urllib
	urllib.urlretrieve ('''http://overpass.osm.rambler.ru/cgi/interpreter?data=relation["route"="trolleybus"](56.917998496857315,40.89179992675781,57.06780339266955,41.119422912597656);(._;>;);out meta;''', "data.osm")


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
	DROP TABLE IF EXISTS planet_osm_buildings CASCADE;
	DROP TABLE IF EXISTS planet_osm_line 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_nodes 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_point 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_polygon CASCADE;
	DROP TABLE IF EXISTS planet_osm_rels 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_roads 	CASCADE;
	DROP TABLE IF EXISTS planet_osm_ways 	CASCADE;
	DROP TABLE IF EXISTS route_line_labels 	CASCADE;
	DROP TABLE IF EXISTS routes_with_refs 	CASCADE;
	DROP TABLE IF EXISTS terminals 		CASCADE;
	DROP TABLE IF EXISTS terminals_export 	CASCADE;

	
	'''

	cur.execute(sql)
	conn.commit()

def update_background():
	dbname='osmdb'
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
	'''

	cur.execute(sql)
	conn.commit()

	

	os.system('''osm2pgsql -s -l -G -C 700 -c -d osmdb -U user --proj 900913 -v  RU-MOW.osm.pbf''')
	#osm2pgsql -s -l -G -C 700 -c -d osmdb -U user  -v --proj 900913 temp.osm


def filter_routes():
	os.system('''
	osmosis --read-pbf RU-KRS.osm.pbf --tag-filter accept-relations route=trolleybus --used-way  --write-xml data.osm
	''')

def importdb():
	os.system('''
	osm2pgsql -s -l -C 700 -c -d osmot -U user  data.osm
	''')

def process():
	os.system('''
	python ../../osmot.py -hs localhost -d osmot -u user -p user
	''')

def render():

	map_name='Иваново. Карта троллейбусных маршрутов ГУП Мосгортранс.'
	bbox_butovo='40.876594,56.922916,41.120919,57.070322'
	bbox_klapan='37.57309,55.566464,37.595197,55.574352'




	bbox=bbox_butovo
	width=str(2500)
	height=str(int(width)*1.4142857)
	

	command='node /usr/share/tilemill/index.js export tram4 overlay.png --format=png --quiet --verbose=off --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	print command
	os.system(command)
	
	quit()

	command='node /usr/share/tilemill/index.js export "OSMBright" background.png --quiet --verbose=off --format=png --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	print command
	os.system(command)

	command='composite overlay.png background.png composite1.png'
	print command
	os.system(command)
	


	bbox=bbox_klapan
	filename="klapan"
	width=str(1100)
	height=str(1100)

	command='node /usr/share/tilemill/index.js export tram4 "'+filename+'_background".png --quiet --verbose=off --format=png --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	os.system(command)
	command='node /usr/share/tilemill/index.js export "OSMBright" "'+filename+'_overlay".png --quiet --verbose=off --format=png --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	os.system(command)
	command='composite '+filename+'_background.png '+filename+'_overlay.png  -quality 95 "'+filename+'.png"'
	print command
	os.system(command)
	command='composite  '+filename+'.png composite1.png -gravity NorthWest -quality 95 "export1.png"'
	print command
	os.system(command)

	datestring=map_name+" Набор данных Openstreetmap от: "+ time.strftime('%d.%m.%Y',time.strptime(time.ctime(os.path.getctime('data.osm'))))+". Дата создания карты: "+time.strftime("%d.%m.%Y")+"."

	command='composite  logo/logo.png export1.png -gravity SouthEast "export2.png"'
	print command
	os.system(command)

	command='convert  logo/logo.png export2.png -gravity SouthEast -annotate "'+datestring+'" "export.png"'
	command='composite logo/logo.png export2.png -gravity SouthEast  export1.png'
	print command
	os.system(command)

	command="convert  export1.png  label:'"+datestring+"'  -gravity SouthWest -flatten export.png"
        print command
	os.system(command)

	command='rm background.png'
	os.system(command)
	command='rm overlay.png'
	os.system(command)
	command='rm export1.png'
	os.system(command)
	command='rm klapan.png'
	os.system(command)
	command='rm '+filename+'_background.png'
	os.system(command)
	command='rm '+filename+'_overlay.png'
	os.system(command)

	command='rm composite1.png'
	os.system(command)
	command='rm export2.png'
	os.system(command)


if __name__ == '__main__':
#	filter_routes()
	cleardb()
	download_osm()
#	update_background()
	importdb()
	process() 
	render()
