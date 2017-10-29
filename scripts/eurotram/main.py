#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: Update and crop osm dump file for Europe
# Author: Artem Svetlov <artem.svetlov@nextgis.com>



import os
import config
import argparse

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('-u', '--update', type=str, choices=['day', 'hour', 'minute'], default='day',
                        help='command for osmupdate')

    parser.epilog = \
        '''Samples:
%(prog)s
''' \
        % {'prog': parser.prog}
    return parser

#if prevdump not exists - download CFO from geofabrik and crop to Europe
def updateDump(update='day',work_dump='dump.osm.pbf'):
    

    
    dump_url='http://download.geofabrik.de/europe-latest.osm.pbf'
    downloaded_dump='europe-latest.osm.pbf'
    updated_dump='osm/just_updated_dump.osm.pbf'
    poly_file='europe.poly'
    directory='osm'
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    #frist run of program
    if os.path.exists(work_dump) == False:
        os.system('wget ' + dump_url)
        os.rename(downloaded_dump, work_dump) 

    #if prevdump dump exists - run osmupdate, it updating it to last hour state with clipping, and save as currentdump
    cmd = 'osmupdate {work_dump}  {updated_dump} --{update}   -v -B={poly_file}'.format(
        work_dump=work_dump,
        updated_dump=updated_dump,
        update=update,
        poly_file=poly_file)
    os.system(cmd)
    
    #if osmupdate not find updates in internet - new file not created, will be used downloaded file
    if os.path.exists(work_dump) == True: 
        #rename currentdump to prevdump
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)

    return 0
    

    
def filter_osm_dump(work_dump='dump.osm.pbf'):
        import json
        import pprint
        pp=pprint.PrettyPrinter(indent=2)

        refs=[]

        file_src = work_dump
        file_temp_1 = 'routes.osm.pbf'
        file_result = 'routesFinal.osm.pbf'
        
        print 'Filter step 1'
        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf {file_src} \
  --tf accept-relations route=tram \
  --used-way --used-node \
  --write-pbf {file_temp_1}
'''.format(file_src=file_src,file_temp_1=file_temp_1)
        os.system(cmd)

        print 'Filter step 3'
        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf {file_temp_1} \
  --tf accept-relations "type=route" \
  --used-way --used-node \
  --write-pbf {file_result}
    '''
        cmd = cmd.format(file_temp_1=file_temp_1,file_result=file_result)
        os.system(cmd)


def importdb(host,database,username,password,filename='routesFinal.osm.pbf'):
    cmd = 'osm2pgsql --create --slim -E 3857 --cache-strategy sparse --cache 100 --host {host} --database {database} --username {username} {filename}'.format(host=host,
    database=database,username=username,password=password,filename=filename)
    print cmd
    os.system(cmd)        

def process(host,dbname,user,password):
    
        cmd='''python ../../osmot.py -hs {host} -d {dbname] -u {user} -p {password}
    '''.format(
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

    update = args.update
    
    updateDump(update)
    filter_osm_dump()
    
    importdb(host,dbname,user,password)
    process(host,dbname,user,password) 
