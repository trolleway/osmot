#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: Update and crop osm dump file for Europe
# Author: Artem Svetlov <artem.svetlov@nextgis.com>



import os
import config
import argparse
import psycopg2
import shutil

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('-u', '--update', type=str, choices=['day', 'hour', 'minute'],
                        help='command for osmupdate')

    parser.epilog = \
        '''Samples:
%(prog)s
''' \
        % {'prog': parser.prog}
    return parser

#if prevdump not exists - download CFO from geofabrik and crop to ROI
def updateDump(update = None,
               dump_url = 'http://download.openstreetmap.fr/extracts/russia/central_federal_district/moscow_oblast-latest.osm.pbf',
               poly_url = 'http://download.geofabrik.de/russia.poly',
               work_dump = 'dump.osm.pbf',
               poly_file = 'bounds.poly'):
    
    if update is None:
        update_command = ''
    else:
        update_command = '--' + update
    
    poly_file = poly_url.split('/')[-1]
    downloaded_dump=dump_url.split('/')[-1]
    updated_dump='osm/just_updated_dump.osm.pbf'

    tempdirectory='osm'   
    if not os.path.exists(tempdirectory):
        os.makedirs(tempdirectory)

    os.system('wget --timestamping ' + dump_url)
    shutil.copy2(downloaded_dump, work_dump) 
        
    os.system('wget  --timestamping '+poly_url)

    #if prevdump dump exists - run osmupdate, it updating it to last hour state with clipping, and save as currentdump
    if os.name == 'nt':
        osmupdate_path = 'osmup'
        print 'Operatins system is Windows. osmupdate.exe is not valid filename at this OS, try call osmup.exe instead'
    else:
        osmupdate_path = 'osmupdate'
    cmd = '{osmupdate_path} {work_dump}  {updated_dump} {update_command}   -v --keep-tempfiles -B={poly_file}'.format(
        work_dump=work_dump,
        updated_dump=updated_dump,
        update_command=update_command,
        poly_file=poly_file,
        osmupdate_path = osmupdate_path)
    print cmd
    os.system(cmd)
    
    #if osmupdate worked good, it create updated_dump file. Work dump will replaced by it
    if os.path.exists(updated_dump) == True: 
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)
    else:
        #osmupdate found your file is already up-to-date
        pass
    
    os.rmdir(tempdirectory)

    return 0
    

    
        
def filter_osm_dump(work_dump='dump.osm.pbf',file_result='routesFinal.osm.pbf'):
        import json
        import pprint
        pp=pprint.PrettyPrinter(indent=2)

        refs=[]

        file_src = work_dump
        file_temp_1 = 'routes_temp.osm.pbf'
        file_result = 'routesFinal.osm.pbf'
        
        o5m='temp.o5m'
        print 'Filter step 1'
        
        cmd='osmconvert {work_dump} -o={o5m}'.format(work_dump=work_dump,o5m=o5m)
        os.system(cmd)
        print 'Filter step 2' 
        #cmd='osmfilter {o5m} --keep="route=tram" --drop="railway=platform public_transport=platform" >temp2.o5m'.format(o5m=o5m)
        cmd='osmfilter {o5m} --keep="route=trolleybus" --drop="railway=platform public_transport=platform" >temp2.o5m'.format(o5m=o5m)
        #cmd='osmfilter {o5m} --keep="route=bus =share_taxi" --drop="railway=platform public_transport=platform" >temp2.o5m'.format(o5m=o5m)
        os.system(cmd)   
        print 'Filter step 3' 
        cmd='osmconvert temp2.o5m -o={file_result}'.format(file_result=file_result)
        os.system(cmd)
        
        os.remove(o5m)
        os.remove('temp2.o5m')

	
def cleardb(host,dbname,user,password):
	#drop with CASCADE
	#not needed since osm2pgsql varsion 0.92.0
	ConnectionString = "host={host} dbname={dbname} user={user} password={password}".format(host=host,dbname=dbname,user=user,password=password)
	try:
		conn = psycopg2.connect(ConnectionString)
	except psycopg2.Error as e:
		print 'I am unable to connect to the database' 
		print e.pgerror
                print ConnectionString
		quit()
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

def importdb(host,database,username,password,filename='routesFinal.osm.pbf'):
    os.system('export PGPASS='+password)
    
    cmd = 'osm2pgsql --create --slim  --cache-strategy sparse --cache 100 --style default.style --host {host} --database {database} --username {username} {filename}'.format(host=host,
    database=database,username=username,password=password,filename=filename)
    print cmd
    os.system(cmd)        




def process(host,dbname,user,password):
    
    cmd = 'python ../../osmot.py -hs {host} -d {dbname} -u {user} -p {password}'
    cmd = cmd.format(
            host=host,
            dbname=dbname,
            user=user,
            password=password)

    os.system(cmd)
        
        
if __name__ == '__main__':
    host=config.host
    dbname=config.dbname
    user=config.user
    password=config.password

        
    parser = argparser_prepare()
    args = parser.parse_args()

    
    if args.update is None:
        update = None
    else:
        update = args.update
    
    updateDump(update,poly_file='europe.poly',dump_url=config.dump_url,poly_url=config.poly_url)
    filter_osm_dump(work_dump='dump.osm.pbf',file_result='routesFinal.osm.pbf')
    
    cleardb(host,dbname,user,password)
    importdb(host,dbname,user,password)
    process(host,dbname,user,password) 
