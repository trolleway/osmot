#!/usr/bin/python
# -*- coding: utf-8 -*-


import psycopg2
import string
import argparse


def deb(string):
    return 0
    print string


def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('-hs', '--host', type=str, default='localhost',
                        help='Postgresql host')
    parser.add_argument('-d', '--database', type=str, default='osmot',
                        help='Postgresql database')
    parser.add_argument('-u', '--username', type=str, default='user',
                        help='Postgresql username')
    parser.add_argument('-p', '--password', type=str, default='user',
                        help='Postgresql password')

    parser.epilog = \
        '''Samples:
%(prog)s /home/someuser/moscow.csv
%(prog)s -t 3 /home/someuser/all_uics/
%(prog)s -t 5 -r RU-SPE /home/someuser/saint-pet.csv
''' \
        % {'prog': parser.prog}
    return parser


def main():

    parser = argparser_prepare()
    args = parser.parse_args()

    dbname = args.database
    username = args.username
    host = args.host
    password = args.password

    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='"
                                + username + "' host='" + host
                                + "' password='" + password + "'")
    except:
        print 'I am unable to connect to the database'
        return 0

    # Create some additional tables in database. My QGIS version does not work with views.....

    cur = conn.cursor()
    cur.execute('''DROP TABLE IF EXISTS terminals''')
    conn.commit()
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

    print '_______________________________________________'
    cur = conn.cursor()

    sql = '''
         DROP TABLE IF EXISTS route_line_labels CASCADE
        ;'''
    cur.execute(sql)
    conn.commit()
    sql = \
        '''
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
        tags::VARCHAR LIKE '%route,trolleybus%'
        OR tags::VARCHAR LIKE '%route,tram%'
        OR tags::VARCHAR LIKE '%route,bus%'
        OR tags::VARCHAR LIKE '%route,share_taxi%'
                ''')
    except:
        return 0

    rows = cur.fetchall()
    for row in rows:
        members_list = row[4][::2]
        roles_list = row[4][1::2]

        current_route_id = row[0]
        deb('Parce relation' + str(current_route_id))
        
        WaysInCurrentRel=[]
        
        #Put in WaysInCurrentRel id's of ways with empty roles
        for i in range(0,len(members_list)):
                member_code=members_list[i]
                member_role=roles_list[i]
                if ((member_code.find('w')>=0) and ((member_role=='') or (member_role=='forward') or (member_role=='backward')  or (member_role=='highway') )):
                        WaysInCurrentRel.append(member_code)
                
        for (idx, item) in enumerate(WaysInCurrentRel):
            if item.find('n'):
                item = item[1:]
                WaysInCurrentRel[idx] = item

        if len(WaysInCurrentRel)<1:
                continue

        # Locate frist point of frist way in route
        WayFrist = WaysInCurrentRel[len(WaysInCurrentRel) - 1]
        WaySecond = WaysInCurrentRel[len(WaysInCurrentRel) - 2]

        sql = \
            '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
            + WayFrist
        try:
            cur.execute(sql)
        except:
            print "I can't SELECT "
        rows2 = cur.fetchall()
        for row2 in rows2:

            f1 = row2[0]
            f2 = row2[1]

        sql = \
            '''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id=''' \
            + WaySecond
        try:
            cur.execute(sql)
        except:
            print "I can't SELECT "
        rows2 = cur.fetchall()
        for row2 in rows2:

            l1 = row2[0]
            l2 = row2[1]

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
        (SELECT substring(tags::varchar from 'ref,(.*?)[,}]') FROM planet_osm_rels WHERE id=''' \
            + str(current_route_id) + ''' )
        )
        ;'''
        cur.execute(sql)
        conn.commit()

    # Calculate route labels

    print 'Create route labels'
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
    for row in rows:
        current_street_count = current_street_count + 1
        way_id = row[0]
        way_street_name = str(row[1])

        # deb('calculate refs for line '+str(way_id)+' '+way_street_name)

        print '' + string.rjust(str(way_id), 10) + ' ' \
            + string.rjust(str(way_street_name.strip()), 60) + ' ' \
            + string.rjust(str(current_street_count) + '/'
                           + str(ways_count_total), 7)

        # For each route, read each way

        sql2 = \
            '''
                SELECT
        id,
        substring(tags::varchar from 'ref,(.*?)[,}]') AS ref,
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
            deb('- relation ' + str(row2[0]) + ' ref=' + str(row2[1])
                + ' name=' + str(row2[2]))
            current_routemaster_ref = row2[1]
            sql3 = \
                '''
        SELECT
        *
        FROM planet_osm_rels                
        WHERE members::VARCHAR LIKE '%''' \
                + str(way_id) + '''%'
        AND id = ''' + str(row2[0]) \
                + '''
                        '''
            cur.execute(sql3)
            rows3 = cur.fetchall()
            for row3 in rows3:
                members_list = row3[4][::2]
                current_rel_id = row[0]

                WaysInCurrentRel = []
                WaysInCurrentRel = [i for i in members_list
                                    if not i.find('w')] # TODO w or n in query?

                # l[1::2] for even elements

                for (idx, item) in enumerate(WaysInCurrentRel):
                    if item.find('n'):
                        item = item[1:]
                        WaysInCurrentRel[idx] = item

                local_way_id_current = 0
                local_way_id_next = 0
                for local_way_id in WaysInCurrentRel:

                    local_way_id_next = local_way_id_current
                    local_way_id_current = local_way_id

                    # deb('-- '+local_way_id)

                    if str(local_way_id) == str(way_id):
                        deb('--- current_way='
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

                            current_direction = 'b'
                            if f2 == l1 or f2 == l2:
                                current_direction = 'f'
                            if current_direction == 'b':
                                function = 'ST_EndPoint'
                                this_way_refs_direction[ref, 'b'] = 1
                            else:
                                function = 'ST_StartPoint'
                                this_way_refs_direction[ref, 'f'] = 1

                            deb('--- direction=' + current_direction)
                        else:

                            # separately calculate direction for last way in route (TODO need refactoring)

                            local_way_id_current = WaysInCurrentRel[0]
                            if len(WaysInCurrentRel) > 1:
                                local_way_id_prev = WaysInCurrentRel[1]
                            else:
                                local_way_id_prev = local_way_id_current
                            deb('-- current=' + local_way_id_current
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
                            for row2 in rows2:
                                p1 = row2[0]
                                p2 = row2[1]

                            current_direction = 'b'
                            if f1 == p2 or f1 == p1:
                                current_direction = 'f'
                            if current_direction == 'b':
                                function = 'ST_EndPoint'
                                this_way_refs_direction[ref, 'b'] = 1
                            else:
                                function = 'ST_StartPoint'
                                this_way_refs_direction[ref, 'f'] = 1

                # separately calculate direction for last way in route (TODO need refactoring)

                local_way_id_current = 0

        sql = \
            '''
                SELECT

        DISTINCT substring(tags::varchar from 'ref,(.*?)[,}]') AS ref
        
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
                    direction_symbol = '-ERROR'

            export_ref = export_ref + ref + direction_symbol + '. '
            export_ref_reverse = export_ref_reverse + ref \
                + direction_symbol_reverse + '. '
            deb('-- ' + ref + ' ' + to + ' direction=' + set_direction)

            if set_direction == 'error':

                exit()
        
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


    cur.execute(sql)
    conn.commit()

    print 'Create terminals table (TODO replace to view)'

    sql='''
SELECT UpdateGeometrySRID('terminals','wkb_geometry',3857);
DROP TABLE if exists terminals_export cascade;
CREATE  table terminals_export AS
        (
        SELECT
        DISTINCT ST_GeomFromWKB(wkb_geometry) AS wkb_geometry,
        ROW_NUMBER() OVER() 				AS terminal_id ,
        name,
        string_agg(routes,',' ORDER BY routes) AS routes,
        concat(
                trim(both '"' from REPLACE(name, '\\\', '')),
		' ',
                '[',
                string_agg(routes,',' ORDER BY routes),
                ']')
                            AS long_text,
        ST_X(wkb_geometry) 	AS label_pos_x,
        ST_Y(wkb_geometry) 	AS label_pos_y,
        '' 			        AS label_align_h,
        '' 			        AS label_align_v,
        2			        AS label_quanrant,
        360			        AS label_angle,
        1                   AS show_label,
        ''                  AS always_show
        FROM terminals
        GROUP BY wkb_geometry, name
        )
        ;
        ALTER TABLE terminals_export ADD PRIMARY KEY (terminal_id);
        SELECT UpdateGeometrySRID('terminals_export','wkb_geometry',3857);


'''

    cur.execute(sql)
    conn.commit()

    print 'Terminals created'

    sql = '''
        DROP TABLE IF EXISTS routes_with_refs
        '''
    cur.execute(sql)
    conn.commit()

    sql = \
        '''
        CREATE OR REPLACE VIEW routes_with_refs AS 
        (SELECT
        ROW_NUMBER() OVER() 				AS id,
        degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))+0 AS angle,
        ST_X(ST_Line_Interpolate_Point(way,0.5)) 	AS x,
        ST_Y(ST_Line_Interpolate_Point(way,0.5)) 	AS y,
        way AS wkb_geometry,
        CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) 
		THEN route_line_labels.route_ref_reverse
        	ELSE route_line_labels.route_ref
        END					        
            AS routes_ref,
        ''  AS rotation,
        ''  AS alignment,
        1   AS show_label,
        ''  AS always_show

        FROM
            planet_osm_line JOIN route_line_labels
        ON (planet_osm_line.osm_id = route_line_labels.osm_id)
        WHERE planet_osm_line.osm_id>0
        )
        '''
	#If view routes_with_refs failed while adding to QGIS with error "an invalid layer" - set while adding table to QGIS field "primary key" 

    cur.execute(sql)
    conn.commit()


if __name__ == '__main__':
    main()
