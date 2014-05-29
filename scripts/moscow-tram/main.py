#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import psycopg2
import time

# Создание картинки с картой маршрутов Московского трамвая
# Необходим tilemill, который будет генерировать подложку, и накладываемую карту линий.


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
	DROP TABLE  IF EXISTS planet_osm_buildings CASCADE;
	DROP TABLE  IF EXISTS planet_osm_line CASCADE;
	DROP TABLE  IF EXISTS planet_osm_nodes CASCADE;
	DROP TABLE  IF EXISTS planet_osm_point CASCADE;
	DROP TABLE  IF EXISTS planet_osm_polygon CASCADE;
	DROP TABLE  IF EXISTS planet_osm_rels CASCADE;
	DROP TABLE  IF EXISTS planet_osm_roads CASCADE;
	DROP TABLE  IF EXISTS planet_osm_ways CASCADE;
	DROP TABLE  IF EXISTS route_line_labels CASCADE;
	DROP TABLE  IF EXISTS routes_with_refs CASCADE;
	DROP TABLE  IF EXISTS terminals CASCADE;
	DROP TABLE  IF EXISTS terminals_export CASCADE;
	DROP TABLE  IF EXISTS routes_refs_positions CASCADE;
	'''

	cur.execute(sql)
	conn.commit()

def importdb():
	os.system('''
	osm2pgsql -s -l -C 700 -c -d osmot -U user  data.osm
	''')

def process():
	os.system('''
	python ../../osmot.py -hs localhost -d osmot -u user -p user
	''')

def render():

	map_name='Москва, карта трамвайных маршрутов'
	bbox_moscow='37.351044,55.590967,37.864431,55.895916'
	bbox_olhovskaya='37.709687,55.777234,37.725591,55.787914'
	bbox_apache='37.518113,55.589584,37.675809,55.740011'
	bbox_apache='37.599738,55.700019,37.628345,55.718214'
	bbox_moscowtrolleybus='37.31684,55.527838,37.911243,55.931893'
	bbox_moscownight='37.355035,55.562704,37.859315,55.994875'
	bbox_moscowcenter='37.59536,55.741689,37.653322,55.769957'
	bbox_paliha='37.582619,55.774988,37.61396,55.79131'

	bbox=bbox_moscow
	width=str(2500)
	height=str(int(width)*1.4142857)
	#

	#Стиль tram4 для tilemill лежит в /styles/mss
	#
	command='node /usr/share/tilemill/index.js export tram4 overlay.png --format=png --quiet --verbose=off --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	print command
	os.system(command)

	command='node /usr/share/tilemill/index.js export "OSMBright" background.png --quiet --verbose=off --format=png --width='+width+' --height='+height+' --bbox="'+bbox+'"'
	print command
	os.system(command)

	command='composite overlay.png background.png composite1.png'
	print command
	os.system(command)
	


	bbox=bbox_paliha
	filename="klapan"

	command='node /usr/share/tilemill/index.js export tram4 "'+filename+'_background".png --quiet --verbose=off --format=png --width=800 --height=800 --bbox="'+bbox+'"'
	os.system(command)
	command='node /usr/share/tilemill/index.js export "OSMBright" "'+filename+'_overlay".png --quiet --verbose=off --format=png --width=800 --height=800 --bbox="'+bbox+'"'
	os.system(command)
	command='composite '+filename+'_background.png '+filename+'_overlay.png  -quality 95 "'+filename+'.png"'
	print command
	os.system(command)
	command='composite  '+filename+'.png composite1.png -gravity NorthEast -quality 95 "export1.png"'
	print command
	os.system(command)

	datestring=map_name+" Набор данных от: "+ time.strftime('%d.%m.%Y',time.strptime(time.ctime(os.path.getctime('data.osm'))))+" Дата визуализации: "+time.strftime("%d.%m.%Y")

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

def filter_label_by_geojson():
	#clear table in db
	
	#load geojson to db
	command='ogr2ogr -f "PostgreSQL" PG:"host=localhost user=user dbname=osmot password=user" osmot_refplaces_moscow_tram.geojson -nln "routes_refs_positions"'
	os.system(command)
	sql='''
	DROP TABLE  IF EXISTS routes_with_refs_2 CASCADE;
	CREATE TABLE routes_with_refs_2 AS (SELECT * FROM routes_with_refs);
	UPDATE routes_with_refs_2
	SET is_show=1
	FROM  routes_refs_positions 
	WHERE ST_Crosses(routes_refs_positions.wkb_geometry , routes_with_refs_2.wkb_geometry);

	SELECT routes_with_refs_2.* 
	FROM routes_with_refs_2
	ORDER BY id;
	''';

	
	#alter route_refs table
	#update route_refs


if __name__ == '__main__':
	cleardb()
	importdb()
	process() 
	#render()
	filter_label_by_geojson()
