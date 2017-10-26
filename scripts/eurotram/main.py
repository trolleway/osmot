#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: Update and crop osm dump file for Europe
# Author: Artem Svetlov <artem.svetlov@nextgis.com>



import os

#if prevdump not exists - download CFO from geofabrik and crop to Europe
def updateDump():
    
    dump_url='http://download.geofabrik.de/europe-latest.osm.pbf'
    downloaded_dump='europe-latest.osm.pbf'
    work_dump='europe-latest-working.osm.pbf'
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
    cmd='osmupdate '+ work_dump + ' ' + updated_dump + ' --hour   -v -B='+poly_file #--day --hour 
    os.system(cmd)
    
    #if osmupdate not find updates in internet - new file not created, will be used downloaded file
    if os.path.exists(work_dump) == True: 
        #rename currentdump to prevdump
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)

    return 0
    
    
if __name__ == '__main__':
        updateDump()

