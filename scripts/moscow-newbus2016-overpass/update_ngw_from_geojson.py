#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: Update a one layer in NextGIS Web from local geojson file
# Author: Artem Svetlov <artem.svetlov@nextgis.com>
# Copyright: 2016, NextGIS <info@nextgis.com>



'''

Update a vector layer in NextGIS Web from local geojson file
Before frist run you should create a layer from this file
Allow deleting, updating and creating features.
Records compared by values and geometry, so only updated records are transferred. 

Usage: update_ngw_from_geojson.py --ngw_url http://trolleway.nextgis.com --ngw_resource_id 35 --ngw_login administrator --ngw_password admin --check_field road_id --filename routes_with_refs.geojson
'''

import os


from osgeo import ogr, gdal
from osgeo import osr

import urllib

import zipfile
import sys
import requests
import pprint
import json

import argparse


def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('-url', '--ngw_url', type=str, default='localhost',
                        help='URL of NextGIS Web instance')
    parser.add_argument('-ngw_resource_id', '--ngw_resource_id', type=str, default='0',
                        help='NextGIS Web resource_id')
    parser.add_argument('-u', '--ngw_login', type=str, default='administrator',
                        help='NextGIS Web username')
    parser.add_argument('-p', '--ngw_password', type=str, default='admin',
                        help='NextGIS Web password')
    parser.add_argument('-cf', '--check_field', type=str, default='road_id',
                        help='Field for compare')

    parser.add_argument('-fn', '--filename', type=str, default='road_id',
                        help='Filename')

    parser.epilog = \
        '''Samples:
%(prog)s --ngw_url http://trolleway.nextgis.com --ngw_resource_id 35 --ngw_login administrator --ngw_password admin --check_field road_id --filename routes_with_refs.geojson

''' \
        % {'prog': parser.prog}
    return parser



class NGWSynchroniser:


    accounts = {}

    def __init__(self,cfg):

        self.ForceToMultiPolygon = True #Не знаю, нужно ли?
        self.delta = 0.00000001 #Using in compare points 
        self.ngw_url = cfg['ngw_url']+'/api/resource/'
        self.resid=cfg['ngw_resource_id']
        self.ngw_creds = (cfg['ngw_login'], cfg['ngw_password'])

     #Taken from wfs2ngw.py
    def compareValues(self,ngw_value, wfs_value):
        if (ngw_value == '' or ngw_value == None) and (wfs_value == '' or wfs_value == None):
            return True
        
        if isinstance(ngw_value, float) and isinstance(wfs_value, float):              
            return abs(ngw_value - wfs_value) < self.delta 
            
        if ngw_value != wfs_value:      
            return False
        return True
        
    def comparePoints(self,ngw_pt, wfs_pt):
        print ngw_pt, wfs_pt

        return (abs(ngw_pt[0] - wfs_pt[0]) < self.delta) and (abs(ngw_pt[1] - wfs_pt[1]) < self.delta)
        
    def compareLines(self,ngw_line, wfs_line):
        if ngw_line.GetPointCount() != wfs_line.GetPointCount():
            return False
        for i in range(ngw_line.GetPointCount()):

            if not self.comparePoints(ngw_line.GetPoint(i), wfs_line.GetPoint(i)):
                return False
            
        return True
        
    def comparePolygons(self,ngw_poly, wfs_poly):
        ngw_poly_rings = ngw_poly.GetGeometryCount()
        wfs_poly_rings = wfs_poly.GetGeometryCount()
        if ngw_poly_rings != wfs_poly_rings:
            return False

        for i in range(ngw_poly_rings):
            if not self.compareLines(ngw_poly.GetGeometryRef(i), wfs_poly.GetGeometryRef(i)):
                return False 





        for i in range(ngw_poly.GetPointCount()):
            if not self.comparePoints(ngw_poly.GetGeometryRef(i), wfs_poly.GetGeometryRef(i)):
                return False

        return True                 
        
    def compareGeom(self,ngw_geom, wfs_geom):  
  
        if ngw_geom.GetGeometryCount() <> wfs_geom.GetGeometryCount():
            return False    #Diffirent geometry count
        elif ngw_geom.GetGeometryType() is ogr.wkbPoint:      
            return self.comparePoints(ngw_geom, wfs_geom)  
        elif ngw_geom.GetGeometryType() is ogr.wkbLineString:
            return self.compareLines(ngw_geom, wfs_geom)  
        elif ngw_geom.GetGeometryType() is ogr.wkbPolygon:
            return self.comparePolygons(ngw_geom, wfs_geom)  
        elif ngw_geom.GetGeometryType() is ogr.wkbMultiPoint:
            for i in range(ngw_geom.GetGeometryCount()):
                if not self.comparePoints(ngw_geom.GetGeometryRef(i).GetPoint(0), wfs_geom.GetGeometryRef(i).GetPoint(0)):
                    return False
        elif ngw_geom.GetGeometryType() is ogr.wkbMultiLineString:
            for i in range(ngw_geom.GetGeometryCount()):
                if not self.compareLines(ngw_geom.GetGeometryRef(i), wfs_geom.GetGeometryRef(i)):
                    return False
        elif ngw_geom.GetGeometryType() is ogr.wkbMultiPolygon:
            for i in range(ngw_geom.GetGeometryCount()):
                if not self.comparePolygons(ngw_geom.GetGeometryRef(i), wfs_geom.GetGeometryRef(i)):
                    return False
        else:

            return True # this is unexpected

        return True     

    def compareFeatures(self,ngw_feature, wfs_feature):
        # compare attributes
        #pp = pprint.PrettyPrinter()       
        #pp.pprint(ngw_feature)
        #pp.pprint(wfs_feature)
        #quit()

        ngw_fields = ngw_feature['fields']
        wfs_fields = wfs_feature['fields']
        for ngw_field in ngw_fields:
            if not self.compareValues(ngw_fields[ngw_field], wfs_fields[ngw_field]):
                return False
        # compare geom
        data=self.compareGeom(ngw_feature['geom'], wfs_feature['geom'])
        return data

    def createPayload(self,wfs_feature):
        payload = {
            'geom': wfs_feature['geom'].ExportToWkt(),
            'fields': wfs_feature['fields']
        }
        return payload

    #Taken from wfs2ngw.py





    def openGeoJson(self,check_field, filename):



        driver = ogr.GetDriverByName("GeoJSON")
        dataSource = driver.Open(filename, 0)
        layer = dataSource.GetLayer()


        wfs_result = dict()
        for feat in layer:
            
            #create geometry object
            geom = feat.GetGeometryRef()
            if geom is not None:
                sr = osr.SpatialReference()
                sr.ImportFromEPSG(3857)
                geom_type = geom.GetGeometryType() #say to Dima
                geom.TransformTo(sr)
                
                if geom_type == ogr.wkbLineString:
                    mercator_geom = ogr.ForceToLineString(geom)
                elif geom_type == ogr.wkbPolygon:
                    mercator_geom = ogr.ForceToPolygon(geom)
                elif geom_type == ogr.wkbPoint:
                    mercator_geom = ogr.ForceToMultiPoint(geom)
                elif geom_type == ogr.wkbMultiPolygon:
                    mercator_geom = ogr.ForceToMultiPolygon(geom)
                elif geom_type == ogr.wkbMultiPoint:
                    mercator_geom = ogr.ForceToMultiPoint(geom)
                elif geom_type == ogr.wkbMultiLineString:
                    mercator_geom = ogr.ForceToMultiPolygon(geom)
                else:            
                    mercator_geom = geom
            else:
                continue
            
            #Read broker fields


            feat_defn = layer.GetLayerDefn()
            wfs_fields = dict()    
            
            for i in range(feat_defn.GetFieldCount()):
                field_defn = feat_defn.GetFieldDefn(i)
                #if field_defn.GetName() == 'gml_id':
                #    continue
                
                #Compare by one control field    
                                 
                if field_defn.GetName() == check_field:
                    check_field_val = feat.GetFieldAsString(i).decode('utf-8')  #GetFieldAsInteger64(i)
                    
                
                #Read fields
                if field_defn.GetType() == ogr.OFTInteger: #or field_defn.GetType() == ogr.OFTInteger64:
                    wfs_fields[field_defn.GetName()] = feat.GetFieldAsInteger(i) #GetFieldAsInteger64(i)
#                    print "%s = %d" % (field_defn.GetName(), feat.GetFieldAsInteger64(i))
                elif field_defn.GetType() == ogr.OFTReal:
                    wfs_fields[field_defn.GetName()] = feat.GetFieldAsDouble(i)
#                    print "%s = %.3f" % (field_defn.GetName(), feat.GetFieldAsDouble(i))
                elif field_defn.GetType() == ogr.OFTString:
#                    print "%s = %s" % (field_defn.GetName(), feat.GetFieldAsString(i))
                    wfs_fields[field_defn.GetName()] = feat.GetFieldAsString(i).decode('utf-8')
                else:
#                    print "%s = %s" % (field_defn.GetName(), feat.GetFieldAsString(i))
                    wfs_fields[field_defn.GetName()] = feat.GetFieldAsString(i).decode('utf-8')
            
            #Object with keys - as values of one control field
            wfs_result[check_field_val] = dict()        
            wfs_result[check_field_val]['id'] = check_field_val      
            wfs_result[check_field_val]['fields'] = wfs_fields
            wfs_result[check_field_val]['geom'] = mercator_geom.Clone()


        layer_result_sorted = dict()
        for key in sorted(wfs_result):
            layer_result_sorted[key]=wfs_result[key]



        return layer_result_sorted

    def GetNGWData(self,code,check_field):

        
        
        #check_field = 'synchronisation_key'
        

        # Put NGW records into array   

        req = requests.get(self.ngw_url + str(self.resid) + '/feature/', auth=self.ngw_creds)
        dictionary = req.json()
        ngw_result = dict()
        geom_type = None
        for item in dictionary:
                objectid = item['fields'][check_field]
                ngw_geom = ogr.CreateGeometryFromWkt(item['geom'])
                if geom_type is None:
                    geom_type = ngw_geom.GetGeometryType()

                #filter here

                ngw_result[objectid] = dict(
                    id=item['id'],
                    geom=ngw_geom,
                    fields=item['fields']
                )
                    
                #sort here
        ngw_result_sorted = dict()
        for key in sorted(ngw_result):
            ngw_result_sorted[key]=ngw_result[key]

 

        return ngw_result_sorted


    def synchronize(self,wfs_result, ngw_result, check_field):

        # compare wfs_result and ngw_result
        
        '''
        Compare ngw records with wfs
        if not compare: put to web (update)
        if ngw result not in wfs: delete from web
        
        Compare wfs records with ngw
        if wfs not in ngw: post to ngw (create)
        
        '''
        import pprint
        pp = pprint.PrettyPrinter()       


        #sort ngw_result
        ngw_result_sorted = dict()
        for key in ngw_result:
            ngw_result_sorted[ngw_result[key]['fields'][check_field]]=ngw_result[key]
        ngw_result = ngw_result_sorted

        #sort wfs_result
        wfs_result_sorted = dict()
        for key in wfs_result:
            wfs_result_sorted[wfs_result[key]['fields'][check_field]]=wfs_result[key]
        wfs_result = wfs_result_sorted

        for ngw_id in ngw_result:
            #ngwFeatureId=ngw_result[ngw_id]['fields'][check_field]
            ngwFeatureId=ngw_result[ngw_id]['id']

            #if ngw_id in wfs_result:
            if wfs_result.has_key(ngw_result[ngw_id]['fields'][check_field]):
                if not self.compareFeatures(ngw_result[ngw_id], wfs_result[ngw_id]):
                    # update ngw feature
                    
                    payload = self.createPayload(wfs_result[ngw_id])
                    req = requests.put(self.ngw_url + str(self.resid) + '/feature/' + str(ngwFeatureId), data=json.dumps(payload), auth=self.ngw_creds)
                    print 'update feature #' + str(ngw_id) + ' ' + str(req)
                print 'same feature: '+str(ngw_id)
            else:
                print 'delete feature ' + str(ngw_id) + ' ngw_feature_id='+str(ngwFeatureId)
                req = requests.delete(self.ngw_url + str(self.resid) + '/feature/' + str(ngwFeatureId), auth=self.ngw_creds)
                
        # add new


        for wfs_id in wfs_result:
            #wfsFeatureId=wfs_result[wfs_id]['fields'][check_field]

            if wfs_id not in ngw_result:
                print 'add new feature #' + str(wfs_id)
                payload = self.createPayload(wfs_result[wfs_id])
                req = requests.post(self.ngw_url + str(self.resid) + '/feature/', data=json.dumps(payload), auth=self.ngw_creds)

    

    








if __name__ == '__main__':

    parser = argparser_prepare()
    args = parser.parse_args()
         
    cfg=dict()
    cfg['ngw_url']=args.ngw_url
    cfg['ngw_resource_id']=args.ngw_resource_id
    cfg['ngw_login']=args.ngw_login
    cfg['ngw_password']=args.ngw_password

    processor=NGWSynchroniser(cfg=cfg)
    print 'Start synchronisation from '+args.filename+' to '+cfg['ngw_url'] + '/resource/'+cfg['ngw_resource_id']


    externalData=processor.openGeoJson(check_field = args.check_field,filename=args.filename)

    print 'Fetching whole ngw layer'
    ngwData=processor.GetNGWData('pa',check_field = args.check_field)
    print 'Compare features'
    processor.synchronize(externalData,ngwData,check_field = args.check_field)
