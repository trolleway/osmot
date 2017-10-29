#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: Update and crop osm dump file for Europe
# Author: Artem Svetlov <artem.svetlov@nextgis.com>



import os

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('-u', '--update', type=str, choices=['day', 'hour', 'minute'] default='day',
                        help='command for osmupdate')

    parser.epilog = \
        '''Samples:
%(prog)s
''' \
        % {'prog': parser.prog}
    return parser

#if prevdump not exists - download CFO from geofabrik and crop to Europe
def updateDump():
    
    parser = argparser_prepare()
    args = parser.parse_args()

    update = args.update
    
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
    
    
if __name__ == '__main__':
        updateDump()

