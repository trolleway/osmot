#!/usr/bin/python
# -*- coding: utf-8 -*-
#test

import psycopg2
import string
import argparse
import sys
import logging
from tqdm import tqdm


#logging.basicConfig(level=logging.WARNING,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

def deb(string):
    logger.debug(string)

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument( '--host', type=str, default='localhost',
                        help='Postgresql host')
    parser.add_argument('--database', type=str, default='gis',
                        help='Postgresql database')
    parser.add_argument('--username', type=str, default='gis',
                        help='Postgresql username')
    parser.add_argument('--password', type=str, default='',
                        help='Postgresql password')
    parser.add_argument('--reverse', action='store_true',
                        help='reverse routes')
    parser.add_argument('--skip-generalization', action='store_true',
                        help='skip clustering terminal points. Clustering works only for EPSG:3857 tables')
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    
    parser.epilog = \
        '''Samples:
%(prog)s
''' \
        % {'prog': parser.prog}
    return parser

def vacuum(conn,tablename):
    logger.debug('running VACUUM')
    old_isolation_level = conn.isolation_level
    conn.set_isolation_level(0)
    query = "VACUUM ANALYZE "+tablename
    cur = conn.cursor()
    cur.execute(query)
    conn.set_isolation_level(old_isolation_level)
    logger.debug('VACUUM finished')

def remove_wrong_ways(ways, pgconn, pgcur):
    #remove from list of ways_ids not downloaded ways and platforms
    
    #optimisation here was not needed yet
    filtered_ways = []
    for way in ways:
        sql = ''' SELECT COUNT(*) AS cnt FROM planet_osm_line WHERE osm_id = {way}; '''
        sql = sql.format(way=way)
        
        pgcur.execute(sql)
        rows = pgcur.fetchall()
        if rows[0][0] > 0: filtered_ways.append(way)
    return filtered_ways

def parse_rels_row(row):
    members_list = row[4][::2]
    roles_list = row[4][1::2]    
    return members_list, roles_list
    
def main():

    parser = argparser_prepare()
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    dbname = args.database
    username = args.username
    host = args.host
    password = args.password
    reverse = args.reverse
    skip_generalization = args.skip_generalization

    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='"
                                + username + "' host='" + host
                                + "' password='" + password + "'")
    except:
        logger.error('I am unable to connect to the database')
        return 0

    # Create some additional tables in database.

    cur = conn.cursor()

    sql = \
        '''
        DROP TABLE IF EXISTS terminals CASCADE;
        CREATE TABLE  terminals (
                 wkb_geometry GEOMETRY,
                 name varchar(250),
                 routes varchar(250),
                 sometype        varchar(250)
        )
        '''
    cur.execute(sql)
    conn.commit()

    cur = conn.cursor()

    sql = \
        '''DROP TABLE IF EXISTS route_line_labels CASCADE;
        CREATE TABLE route_line_labels
        (
         id serial,
         osm_id bigint,
         route_ref text,
         route_ref_reverse text,
	show_label smallint DEFAULT 1
        )
        ;
        '''
    cur.execute(sql)
    conn.commit()

    # Calculate terminal points of routes
    # Selecting routes

    try:
        cur.execute('''
        SELECT
        *
        FROM planet_osm_rels
        WHERE
        tags::VARCHAR LIKE '%route,%'
                ''')
    except:
        return 0

    
    rows = cur.fetchall()
    for row in rows:
        members_list,roles_list = parse_rels_row(row)
        #members_list = row[4][::2]
        #roles_list = row[4][1::2]

        current_route_id = row[0]
        logger.debug('Parce relation' + str(current_route_id))

        WaysInCurrentRel=[]

        #Put in WaysInCurrentRel id's of ways with empty roles
        for i in range(0,len(members_list)):
            member_code=members_list[i]
            member_role=roles_list[i]
            # if member is way, and role in list
            if ((member_code.find('w')>=0) and (member_role in ('','forward','backward','highway') )):
                    WaysInCurrentRel.append(member_code)

        if reverse:
            WaysInCurrentRel.reverse()
        for (idx, item) in enumerate(WaysInCurrentRel):
            if item.find('n'):
                item = item[1:]
                WaysInCurrentRel[idx] = item

        if len(WaysInCurrentRel)<2:
                continue
        #remove from WaysInCurrentRel not downloaded ways and platforms
        
        WaysInCurrentRel = remove_wrong_ways(ways = WaysInCurrentRel, pgconn=conn, pgcur = cur)
    
        # Locate frist point of frist way in route
        WayFrist = WaysInCurrentRel[0]
        WaySecond = WaysInCurrentRel[1]

        sql = \
            '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
            + WayFrist
        try:
            cur.execute(sql)
        except:
            logger.error("I can't SELECT ")
        rows2 = cur.fetchall()
        for row2 in rows2:

            f1 = row2[0]
            f2 = row2[1]
        assert 'f2' in vars() or 'f2' in globals(), 'Not found frist point of line {WayFrist}. Prorably pbf file is invalid. All members of route relations should be in pbf file.'.format(WayFrist=WayFrist)

        sql = \
            '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
            + WaySecond
        try:
            cur.execute(sql)
        except:
            logger.error("I can't SELECT ")
        rows2 = cur.fetchall()
        for row2 in rows2:

            l1 = row2[0]
            l2 = row2[1]

        #compare end nodes of lines by geometry
        #try:
        #    f2
        #except NameError:
        #    raise ValueError('Not found frist point of line {WaySecond}. Prorably pbf file is invalid. All members of route relations should be in pbf file.'.format(WaySecond=WaySecond))
        
        current_direction = 'b'
        if f2 == l1 or f2 == l2:
            current_direction = 'f'

        if current_direction == 'b':
            function = 'ST_EndPoint'
        else:
            function = 'ST_StartPoint'

    # store terminal in database....

        sql = \
            '''
        INSERT INTO terminals (wkb_geometry,name, routes) VALUES
        (
        (SELECT ''' \
            + function + '''(way) FROM planet_osm_line WHERE osm_id=''' \
            + WayFrist \
            + ''' LIMIT 1),
        (SELECT substring(tags::varchar from 'from,(.*?)[,}]') FROM planet_osm_rels WHERE id=''' \
            + str(current_route_id) \
            + ''' LIMIT 1),
        (SELECT substring(tags::varchar from '[^:]ref,(.*?)[,}]') FROM planet_osm_rels WHERE id=''' \
            + str(current_route_id) + ''' )
        )
        ;'''
        cur.execute(sql)
        conn.commit()

    # Calculate route labels

    logger.info('Create route labels')
    this_way_refs_direction = {}

    cur.execute('''
        SELECT
        COUNT(*) AS cnt
        FROM planet_osm_line
        WHERE osm_id > 0
                ''')
    rows = cur.fetchall()
    for row in rows:
        ways_count_total = row[0]

    cur.execute('''
        SELECT
        osm_id, name
        FROM planet_osm_line
        WHERE osm_id > 0
        ORDER BY name DESC
                ''')

    rows = cur.fetchall()

    current_street_count = 0
    pbar = tqdm(total=ways_count_total)
    for row in rows:
        current_street_count = current_street_count + 1
        way_id = row[0]
        way_street_name = str(row[1])

        # logger.debug('calculate refs for line '+str(way_id)+' '+way_street_name)

        pbar.update(1)
        pbar.set_description(str.rjust(str(way_id), 10) + ' ' + way_street_name.strip())
        # For each route, read each way

        sql2 = \
            '''
                SELECT
        id,
        substring(tags::varchar from '[^:]ref,(.*?)[,}]') AS ref,
        substring(tags::varchar from 'name,(.*?)[,}]') AS name
        FROM planet_osm_rels
        WHERE members::VARCHAR LIKE '%''' \
            + str(way_id) + '''%'
        ORDER BY ref;
        '''

        cur.execute(sql2)
        rows2 = cur.fetchall()
        reflist = []

        # for each routemaster for this way

        this_way_refs_direction = {}
        for row2 in rows2:
            ref = str(row2[1])
            logger.debug('- relation ' + str(row2[0]) + ' ref=' + str(row2[1])
                + ' name=' + str(row2[2]))
            current_routemaster_ref = row2[1]
            sql3 = \
                '''
        SELECT
        *
        FROM planet_osm_rels
        WHERE
               id = ''' + str(row2[0]) \
                + '''
                        '''
            cur.execute(sql3)
            rows3 = cur.fetchall()
            for row3 in rows3:
                members_list,roles_list = parse_rels_row(row3)
                
                if reverse:
                    members_list.reverse()
                current_rel_id = row[0]
                
                WaysInCurrentRel = []
                #WaysInCurrentRel = [i for i in members_list
                #                    if not i.find('w')] # TODO w or n in query?

                # l[1::2] for even elements
                
                for i in range(0,len(members_list)):
                    member_code=members_list[i]
                    member_role=roles_list[i]
                    # if member is way, and role in list
                    if ((member_code.find('w')>=0) and (member_role in ('','forward','backward','highway') )):
                            WaysInCurrentRel.append(member_code)
                
                for (idx, item) in enumerate(WaysInCurrentRel):
                    if item.find('n'):
                        item = item[1:] # items start through the rest of the array
                        WaysInCurrentRel[idx] = item

                local_way_id_current = 0
                local_way_id_next = 0
                for local_way_id in WaysInCurrentRel:

                    local_way_id_next = local_way_id_current
                    local_way_id_current = local_way_id



                    if str(local_way_id) == str(way_id):
                        logger.debug('--- current_way='
                            + str(local_way_id_current) + ' next='
                            + str(local_way_id_next))

                        if local_way_id_next != 0:

                            sql = \
                                '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
                                + local_way_id_current
                            cur.execute(sql)
                            rows2 = cur.fetchall()
                            for row2 in rows2:
                                f1 = row2[0]
                                f2 = row2[1]

                            sql = \
                                '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
                                + local_way_id_next
                            cur.execute(sql)
                            rows2 = cur.fetchall()
                            for row2 in rows2:
                                l1 = row2[0]
                                l2 = row2[1]

                            current_direction = 'f'
                            if f2 == l1 or f2 == l2:
                                current_direction = 'b'
                            if current_direction == 'f':
                                function = 'ST_EndPoint'
                                this_way_refs_direction[ref, 'f'] = 1
                            else:
                                function = 'ST_StartPoint'
                                this_way_refs_direction[ref, 'b'] = 1

                            logger.debug('--- direction=' + current_direction)
                        else:

                            # separately calculate direction for last way in route (TODO need refactoring)

                            local_way_id_current = WaysInCurrentRel[0]
                            if len(WaysInCurrentRel) > 1:
                                local_way_id_prev = WaysInCurrentRel[1]
                            else:
                                local_way_id_prev = local_way_id_current
                            logger.debug('-- current=' + local_way_id_current
                                + ' prev=' + local_way_id_prev)


                            sql = \
                                '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
                                + local_way_id_current
                            cur.execute(sql)
                            rows2 = cur.fetchall()
                            for row2 in rows2:
                                f1 = row2[0]
                                f2 = row2[1]

                            sql = \
                                '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
                                + local_way_id_prev
                            cur.execute(sql)
                            rows2 = cur.fetchall()
                            p1 = None
                            p2 = None
                            for row2 in rows2:
                                p1 = row2[0]
                                p2 = row2[1]

                            current_direction = 'f'
                            if p1 is not None:  #if this is refrence to not download way - let it be forward                              
                                if f1 == p2 or f1 == p1:
                                    current_direction = 'b'
                            if current_direction == 'f':
                                function = 'ST_EndPoint'
                                this_way_refs_direction[ref, 'f'] = 1
                            else:
                                function = 'ST_StartPoint'
                                this_way_refs_direction[ref, 'b'] = 1
                            
                            del p1
                            del p2
                # separately calculate direction for last way in route (TODO need refactoring)

                local_way_id_current = 0

        sql = \
            '''
                SELECT

        DISTINCT substring(tags::varchar from '[^:]ref,(.*?)[,}]') AS ref

        FROM planet_osm_rels
        WHERE members::VARCHAR LIKE '%w''' \
            + str(way_id) + '''%'
        ORDER BY ref;
        '''

        cur.execute(sql)
        rows4 = cur.fetchall()
        ref = ''
        export_ref = ''
        export_ref_reverse = ''

        # for each routemaster for this way

        for row4 in rows4:
            ref = str(row4[0])

            # to=str(row4[1])

            to = 'tuda'

            # substring(tags::varchar from 'to,(.*?)[,}]') AS to

            deb('ref=' + ref)
            deb('f is' + str(this_way_refs_direction.get((ref, 'f'),
                0)) + str(this_way_refs_direction.get((ref, 'f'), 0)))
            deb('b is' + str(this_way_refs_direction.get((ref, 'b'),
                0)) + str(this_way_refs_direction.get((ref, 'b'), 0)
                == 1))
            set_direction = 'UNDEF'
            direction_symbol = ''
            direction_symbol_reverse = ''
            if this_way_refs_direction.get((ref, 'f'), 0) \
                & this_way_refs_direction.get((ref, 'b'), 0):
                set_direction = 'both'
                direction_symbol = ''
                direction_symbol_reverse = ''
            elif int(this_way_refs_direction.get((ref, 'f'), 0)) > 0 \
                & this_way_refs_direction.get((ref, 'b'), 0) == 0:

                set_direction = 'forward'
                direction_symbol = '>'
                direction_symbol_reverse = '<'
            elif this_way_refs_direction.get((ref, 'f'), 0) == 0:

                if this_way_refs_direction.get((ref, 'b'), 0) == 1:
                    set_direction = 'backward'
                    direction_symbol = '<'
                    direction_symbol_reverse = '>'
                elif this_way_refs_direction.get((ref, 'f'), 0) == 0 \
                    & this_way_refs_direction.get((ref, 'b'), 0) == 0:

                    set_direction = 'error'
                    direction_symbol = ''
                    direction_symbol_reverse = ''

            if set_direction != 'error':
                export_ref = export_ref + ref + direction_symbol + '. '
                export_ref_reverse = export_ref_reverse + ref \
                    + direction_symbol_reverse + '. '
                deb('-- ' + ref + ' ' + to + ' direction=' + set_direction)

            #assert set_direction != 'error'


        export_ref=export_ref.rstrip('. ')
        export_ref_reverse=export_ref_reverse.rstrip('. ')
        sql = \
            '''
        INSERT INTO route_line_labels
        (osm_id, route_ref, route_ref_reverse)
        VALUES
        (
        ''' \
            + str(way_id) + ''',
        \'''' + export_ref + '''\',
        \'''' \
            + export_ref_reverse + '''\'

        )

                '''

        cur.execute(sql)
        conn.commit()

    pbar.close()
    
    cur.execute(sql)
    conn.commit()

    logger.info('Create terminals table')

    if skip_generalization:
        sql='''

DROP TABLE if exists terminals_export cascade;
CREATE  table terminals_export AS
        (
        SELECT
        DISTINCT ST_GeomFromWKB(wkb_geometry) AS wkb_geometry,
        ROW_NUMBER() OVER() ::varchar AS terminal_id,
        name,
        string_agg(routes,',' ORDER BY routes) AS routes,
        concat(
                trim(both '"' from REPLACE(name, '\\\', '')),
		' ',
                '[',
                string_agg(routes,',' ORDER BY NULLIF(regexp_replace(routes, '\D', '', 'g'), '')::int),
                ']')
                            AS long_text
        FROM terminals
        GROUP BY wkb_geometry, name
        )
        ;
        ALTER TABLE terminals_export ADD PRIMARY KEY (terminal_id);



'''
    else:
        sql='''
DROP TABLE IF EXISTS terminals_clustered;

--cluster distance set here
CREATE TEMPORARY TABLE terminals_clustered AS
SELECT unnest(ST_ClusterWithin(wkb_geometry, 300)) AS geometrycollection
  FROM terminals;

DROP TABLE IF EXISTS terminals_export CASCADE;
CREATE TABLE terminals_export AS
SELECT
 ST_Centroid(geometrycollection) AS wkb_geometry,
 row_number() over () AS terminal_id,
  --ST_MinimumBoundingCircle(geometrycollection) AS circle,
  (array_agg(terminals.name))[1] AS name,
string_agg(terminals.routes,',' ORDER BY routes) AS routes,
concat(
                trim(both '"' from REPLACE((array_agg(terminals.name))[1], '\\\', '')),
		' ',
                '[',
                string_agg(routes,',' ORDER BY NULLIF(regexp_replace(routes, '\D', '', 'g'), '')::int),
                ']')
                            AS long_text
FROM terminals_clustered
  JOIN terminals
  ON ST_Intersects(ST_Buffer(ST_MinimumBoundingCircle(geometrycollection),300),terminals.wkb_geometry)
--this returns data from all single terminal points in cluster

GROUP BY geometrycollection;

DROP TABLE terminals_clustered;
        '''


    cur.execute(sql)
    conn.commit()

    sql = 'DROP TABLE terminals; ALTER TABLE terminals_export RENAME TO terminals;'
    cur.execute(sql)
    conn.commit()

    '''

    '''
    logger.info('Terminals created')

    #sql = '''
    #    DROP TABLE IF EXISTS routes_with_refs CASCADE;
    #    '''
    #cur.execute(sql)
    #conn.commit()

    sql = \
        '''
        DROP TABLE IF EXISTS routes CASCADE;
        CREATE  TABLE routes AS
        (SELECT
        distinct planet_osm_line.osm_id 	::varchar	AS road_id,
        degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))+0 AS angle,
        ST_X(ST_Line_Interpolate_Point(way,0.5)) 	AS x,
        ST_Y(ST_Line_Interpolate_Point(way,0.5)) 	AS y,
        way AS wkb_geometry,
        CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90)
		THEN route_line_labels.route_ref_reverse
        	ELSE route_line_labels.route_ref
        END
            AS routes_ref
        --,
        --''  AS rotation,
        --''  AS alignment,
        --1   AS show_label,
        --''  AS always_show

        FROM
            planet_osm_line JOIN route_line_labels
        ON (planet_osm_line.osm_id = route_line_labels.osm_id)
        WHERE planet_osm_line.osm_id>0 AND route_line_labels.route_ref <> ''
        );
        ALTER TABLE routes ADD PRIMARY KEY (road_id);
        '''
    #routes is a table, not view, to use primary key for qgis. Views cannot have primary keys
	#If routes failed while adding to QGIS with error "an invalid layer" - set while adding table to QGIS field "primary key"

    cur.execute(sql)
    conn.commit()


if __name__ == '__main__':
    main()
