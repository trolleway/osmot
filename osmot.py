#!/usr/bin/python2.4
#
# 
#

#sudo mount -t vboxsf -o uid=user,rw GIS /home/user/GIS


#osm2pgsql -s -l -C 700 -c -d h09 -U user  vidnoe.osm


def deb(string):
	return 0
	print string
	
import psycopg2
import string

try:
    conn = psycopg2.connect("dbname='h09' user='user' host='localhost' password='user'")
except:
    print "I am unable to connect to the database"
	
	
	
print 'create terminals table'	

cur = conn.cursor()

cur.execute('''TRUNCATE terminals 	''')	
conn.commit()
	
'''
cur.execute(
CREATE TABLE IF NOT exists terminals (
     geom    GEOMETRY,
     name   varchar(250),
     routes   varchar(250),
	 sometype	varchar(250)
)
	
	)	
	
conn.commit()
'''
	
	
print '_______________________________________________'
cur = conn.cursor()



sql='''
 DROP  TABLE IF EXISTS route_line_labels CASCADE
;'''
cur.execute(sql)
conn.commit()		
sql='''
CREATE TABLE route_line_labels
(
  id serial,
  osm_id bigint,
  route_ref text,
  route_ref_reverse text
  
)
;
'''
cur.execute(sql)
conn.commit()	



try:
    cur.execute('''
SELECT 
* 
FROM planet_osm_rels
WHERE tags::VARCHAR LIKE '%route,trolleybus%'

	''')
except:
    print "I can't SELECT from bar"

rows = cur.fetchall()
for row in rows:
	members_list = row[4][::2]
	current_route_id=row[0]
	deb( "Parce relation"+str(current_route_id))
	
	WaysInCurrentRel = [i for i in members_list if not i.find('w') ] #TODO w or n in query?
	#l[1::2] for even elements
	for idx, item in enumerate(WaysInCurrentRel):
	   if item.find('n'):
		   item = item[1:]
		   WaysInCurrentRel[idx] = item
	
	
	WayFrist=WaysInCurrentRel[len(WaysInCurrentRel)-1]
	WaySecond=WaysInCurrentRel[len(WaysInCurrentRel)-2]
	
	
	
	
	'''
				// если конец первой = концу второй, то вперёд
				// если конец первой = началу второй, то вперёд
				//--------------
				// если начало первой = концу второй то назад     
				// если начало первой = началу второй то назад
				
			
				$f1 = $this->id_frist_point_of_way($ways_list,$way1);
				$f2 = $this->id_frist_point_of_way($ways_list,$way2);
				$l1 = $this->id_last_point_of_way($ways_list,$way1);
				$l2 = $this->id_last_point_of_way($ways_list,$way2);
				
				if (is_null($way2)) return FORWARD;  // this is a last segment in route
				if (($l1 == $l2) OR ($l1 == $f2))
				{
					
				#	echo "$f1 $f2 $l1 $l2  FORWARD\n";
					return FORWARD;
				}
				else 
				{
				#	echo "$f1 $f2 $l1 $l2 BACK\n";
					return BACK;
				}	
				'''
	

	
	sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+WayFrist
	
	try:
		cur.execute(sql)
	except:
		print "I can't SELECT "
	rows2 = cur.fetchall()
	for row2 in rows2:

		f1=row2[0]
		f2=row2[1]
		
	sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+WaySecond
	
	try:
		cur.execute(sql)
	except:
		print "I can't SELECT "
	rows2 = cur.fetchall()
	for row2 in rows2:

		l1=row2[0]
		l2=row2[1]
	
	
	current_direction = 'b'
	if (f2 == l1) or (f2 == l2):
		current_direction = 'f'
	
	
	if current_direction=='b':
		function='ST_EndPoint'
	else:	
		function='ST_StartPoint'
	
	
	sql='''
INSERT INTO terminals (geom,name, routes) VALUES 
(
(SELECT '''+function+'''(way) FROM planet_osm_line WHERE osm_id='''+WayFrist+''' LIMIT 1), 
(SELECT substring(tags::varchar from 'from,(.*?)[,}]') FROM planet_osm_rels WHERE id='''+str(current_route_id)+''' LIMIT 1),
(SELECT substring(tags::varchar from 'ref,(.*?)[,}]') FROM planet_osm_rels WHERE id='''+str(current_route_id)+''' )
)
;'''
	cur.execute(sql)
	conn.commit()
	

print "Create route labels"
this_way_refs_direction={}

cur.execute('''
SELECT 
COUNT(*) AS cnt
FROM planet_osm_line
WHERE osm_id > 0



	''')
rows = cur.fetchall()	
for row in rows:
	ways_count_total=row[0]


cur.execute('''
SELECT 
osm_id, name 
FROM planet_osm_line
WHERE osm_id > 0
ORDER BY name
	''')

rows = cur.fetchall()

current_street_count=0
for row in rows:
	current_street_count = current_street_count+1
	way_id=  row[0]	
	way_street_name = str(row[1])
	#deb('calculate refs for line '+str(way_id)+' '+way_street_name)
	print ''+string.ljust(str(way_id),16)+' '+string.ljust(str(way_street_name.strip()),50)+' ' +  string.rjust(str(current_street_count)+'/'+str(ways_count_total),6)
	
	sql2='''
	SELECT 
id,
substring(tags::varchar from 'ref,(.*?)[,}]') AS ref,
substring(tags::varchar from 'name,(.*?)[,}]') AS name
FROM planet_osm_rels 
WHERE members::VARCHAR LIKE '%'''+str(way_id)+'''%'
ORDER BY ref;
'''	
	#get all 

	cur.execute(sql2)
	rows2 = cur.fetchall()
	reflist=[]
	
	#for each routemaster for this way
	this_way_refs_direction={}
	for row2 in rows2:
		ref=str(row2[1])
		deb('- relation '+str(row2[0])+' ref='+str(row2[1])+' name='+str(row2[2]) )
		current_routemaster_ref = row2[1]
		sql3='''
SELECT 
* 
FROM planet_osm_rels		
WHERE members::VARCHAR LIKE '%'''+str(way_id)+'''%'
AND id = '''+str(row2[0])+'''
		'''
		cur.execute(sql3)
		rows3 = cur.fetchall()
		for row3 in rows3:
			members_list = row3[4][::2]
			current_rel_id=row[0]
			#deb('-- relation '+str(row3[0])+' ref='+str(row2[1]))
			
			WaysInCurrentRel=[]
			WaysInCurrentRel = [i for i in members_list if not i.find('w') ] #TODO w or n in query?
			#l[1::2] for even elements
			for idx, item in enumerate(WaysInCurrentRel):
			   if item.find('n'):
				   item = item[1:]
				   WaysInCurrentRel[idx] = item

			
			local_way_id_current=0
			local_way_id_next=0
			for local_way_id in WaysInCurrentRel:
			
				local_way_id_next=local_way_id_current
				local_way_id_current=local_way_id
				#deb('-- '+local_way_id)
				if str(local_way_id)==str(way_id): 
					deb('--- current_way='+str(local_way_id_current)+' next='+str(local_way_id_next))
					
					if local_way_id_next<>0:

						sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+local_way_id_current
						cur.execute(sql)
						rows2 = cur.fetchall()
						for row2 in rows2:
							f1=row2[0]
							f2=row2[1]
							
						sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+local_way_id_next
						cur.execute(sql)
						rows2 = cur.fetchall()
						for row2 in rows2:
							l1=row2[0]
							l2=row2[1]

						current_direction = 'b'
						if (f2 == l1) or (f2 == l2):
							current_direction = 'f'						
						if current_direction=='b':
							function='ST_EndPoint'
							this_way_refs_direction[ref,'b']=1
						else:	
							function='ST_StartPoint'
							this_way_refs_direction[ref,'f']=1
			
						deb('--- direction='+current_direction)
					
					else:
						#separately calculate direction for last way in route (TODO need refactoring)
						local_way_id_current = WaysInCurrentRel[0]
						if len(WaysInCurrentRel)>1:
							local_way_id_prev = WaysInCurrentRel[1]
						else:
							local_way_id_prev = local_way_id_current
						deb('-- current='+local_way_id_current+'    prev='+local_way_id_prev)
						
						sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+local_way_id_current
						cur.execute(sql)
						rows2 = cur.fetchall()
						for row2 in rows2:
							f1=row2[0]
							f2=row2[1]
							
						sql='''SELECT ST_StartPoint(way), ST_EndPoint(way) from planet_osm_line WHERE osm_id='''+local_way_id_prev
						cur.execute(sql)
						rows2 = cur.fetchall()
						for row2 in rows2:
							p1=row2[0]
							p2=row2[1]

						current_direction = 'b'
						if (f1 == p2) or (f1 == p1):
							current_direction = 'f'						
						if current_direction=='b':
							function='ST_EndPoint'
							this_way_refs_direction[ref,'b']=1
						else:	
							function='ST_StartPoint'
							this_way_refs_direction[ref,'f']=1
						
						
						
						
			#separately calculate direction for last way in route (TODO need refactoring)
			
			local_way_id_current=0
			
			
			
		
		
		
	
		
	
	
	
	sql='''
	SELECT 

DISTINCT substring(tags::varchar from 'ref,(.*?)[,}]') AS ref
 
FROM planet_osm_rels 
WHERE members::VARCHAR LIKE '%w'''+str(way_id)+'''%'
ORDER BY ref;
'''		
	
	cur.execute(sql)
	rows4 = cur.fetchall()
	ref=''
	export_ref=''
	export_ref_reverse=''
	
	#for each routemaster for this way
	for row4 in rows4:
		ref=str(row4[0])
		#to=str(row4[1])
		to='tuda'
		#substring(tags::varchar from 'to,(.*?)[,}]') AS to
		deb('ref='+ref)
		deb('f is'+str(this_way_refs_direction.get((ref,'f'),0))+str(this_way_refs_direction.get((ref,'f'),0)))
		deb('b is'+str(this_way_refs_direction.get((ref,'b'),0))+str(this_way_refs_direction.get((ref,'b'),0)==1))
		set_direction='UNDEF'
		direction_symbol=''
		direction_symbol_reverse=''
		if this_way_refs_direction.get((ref,'f'),0) & this_way_refs_direction.get((ref,'b'),0):
			set_direction='both'
			direction_symbol=''	
			direction_symbol_reverse=''	
					
			
		elif int(this_way_refs_direction.get((ref,'f'),0))>0 & this_way_refs_direction.get((ref,'b'),0)==0:
			set_direction='forward'
			direction_symbol='>'
			direction_symbol_reverse='<'
					
		elif this_way_refs_direction.get((ref,'f'),0)==0: 
			if this_way_refs_direction.get((ref,'b'),0)==1:
				set_direction='backward'
				direction_symbol='<'
				direction_symbol_reverse='>'
				
		
			elif this_way_refs_direction.get((ref,'f'),0)==0 & this_way_refs_direction.get((ref,'b'),0)==0:
				set_direction='error'
				direction_symbol='-ERROR'
		
		
		export_ref=export_ref+ref+direction_symbol+'. '
		export_ref_reverse=export_ref_reverse+ref+direction_symbol_reverse+'. '
		deb ('-- '+ref+' '+to+' direction='+set_direction)
		
		if (set_direction=='error'):
			
			exit()
		
		
		

	sql='''
INSERT INTO route_line_labels 
(osm_id, route_ref, route_ref_reverse)
VALUES
(
'''+str(way_id)+''',
\''''+export_ref+'''\',
\''''+export_ref_reverse+'''\'

)

	'''
	
	cur.execute(sql)
	conn.commit()	
	#for local_ref in this_way_refs_direction:
	    
	#a.get((1,'s'))
		

	


cur.execute(sql)
conn.commit()	
	
	
	
print "Create terminals table (TODO replace to view)"	
sql='''
DROP TABLE IF EXISTS terminals_export 
;'''
cur.execute(sql)
conn.commit()		
sql='''
CREATE TABLE terminals_export AS 
(
SELECT 
DISTINCT geom,
name, 
string_agg(routes,'.'), 
concat(name,'  ',string_agg(routes,'.') ) AS long_text
from terminals
GROUP BY geom, name

)
;'''
cur.execute(sql)
conn.commit()
	
	
	
	
	



sql='''
DROP TABLE IF EXISTS lines_refs_test 
'''
cur.execute(sql)
conn.commit()

sql='''
CREATE TABLE lines_refs_test AS
(SELECT * FROM planet_osm_line
WHERE osm_id>0)
'''
cur.execute(sql)
conn.commit()

sql='''
ALTER TABLE lines_refs_test ADD COLUMN route_ref text;
'''
cur.execute(sql)
conn.commit()

sql='''
UPDATE lines_refs_test  
SET route_ref = route_line_labels.route_ref
FROM route_line_labels 
WHERE route_line_labels.osm_id = lines_refs_test.osm_id
'''
cur.execute(sql)
conn.commit()


sql='''
DROP TABLE IF EXISTS lines_refs_test_2 
'''
cur.execute(sql)
conn.commit()

sql='''
CREATE TABLE lines_refs_test_2 AS
(SELECT 
planet_osm_line.osm_id,
ST_MakeLine(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)) AS geom,


	CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) THEN degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90+180 
	ELSE degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90
	END
	AS angl,

degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))+0 AS angl_qgis,
ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)) AS angl_azimut,
360-((atan2(ST_Y(ST_Line_Interpolate_Point(way,0.501))- ST_Y(ST_Line_Interpolate_Point(way,0.5)),ST_X(ST_Line_Interpolate_Point(way,0.501))- ST_X(ST_Line_Interpolate_Point(way,0.5)))+ (2*Pi()))* 180/Pi()) AS angl2,
ST_X(ST_Line_Interpolate_Point(way,0.5)) AS x,
ST_Y(ST_Line_Interpolate_Point(way,0.5)) AS y,

	CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) THEN route_line_labels.route_ref_reverse 
	ELSE route_line_labels.route_ref 
	END
	AS routes_ref_normal,

'blablalba' AS routes_ref_dumb
FROM 
planet_osm_line JOIN route_line_labels
ON (planet_osm_line.osm_id = route_line_labels.osm_id)
WHERE planet_osm_line.osm_id>0
)
'''

'''
	CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) THEN route_line_labels.route_ref_reverse 
	ELSE route_line_labels.route_ref 
	END
	AS routes_ref_normal,
	'''
cur.execute(sql)
conn.commit()



sql='''
DROP TABLE IF EXISTS lines_refs_test_3 
'''
cur.execute(sql)
conn.commit()

sql='''
CREATE TABLE lines_refs_test_3 AS
(SELECT 
planet_osm_line.osm_id,

	
	CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) THEN ST_Reverse(way)
	ELSE way
	END
	AS geom,

degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))+0 AS angl_qgis,
ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)) AS angl_azimut,
360-((atan2(ST_Y(ST_Line_Interpolate_Point(way,0.501))- ST_Y(ST_Line_Interpolate_Point(way,0.5)),ST_X(ST_Line_Interpolate_Point(way,0.501))- ST_X(ST_Line_Interpolate_Point(way,0.5)))+ (2*Pi()))* 180/Pi()) AS angl2,
ST_X(ST_Line_Interpolate_Point(way,0.5)) AS x,
ST_Y(ST_Line_Interpolate_Point(way,0.5)) AS y,

	CASE WHEN (degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 > 90 OR degrees(ST_azimuth(ST_Line_Interpolate_Point(way,0.5),ST_Line_Interpolate_Point(way,0.501)))-90 >90) THEN route_line_labels.route_ref_reverse 
	ELSE route_line_labels.route_ref 
	END
	AS routes_ref_normal,

'blablalba' AS routes_ref_dumb
FROM 
planet_osm_line JOIN route_line_labels
ON (planet_osm_line.osm_id = route_line_labels.osm_id)
WHERE planet_osm_line.osm_id>0
)
'''

cur.execute(sql)
conn.commit()

