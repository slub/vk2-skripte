# -*- coding: utf-8 -*- 
'''
Created on Oct 14, 2013

@author: mendt

This scripts fetch the zoomify properties file from url and parse the width height
'''
# import database stuff 
from sqlalchemy import create_engine
from utils.messtischblatt import initialize_sql, Messtischblatt
from settings import sqlalchemy_engine

# import stuff for searching directory 
import logging
import urllib2
import xml.etree.ElementTree as ET


def parseMtbName(name):
    if 'ORG' in name:
        newString = name[:name.find('ORG')-1]
        return newString
    else:
        newString = name[:name.rfind('.')]
        return newString

def fileType(name):
    if 'jpg' in name:
        return 'jpg'
    elif 'tif' in name:
        return 'tif'
    else:
        return None
    
       
''' main function '''  
def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

    
    # initialize the database with the models
    engine = create_engine(sqlalchemy_engine, encoding='utf8', echo=True)
    dbsession = initialize_sql(engine)
    
    # get a collection of all mtbs object
    mtbs = Messtischblatt.all(dbsession)
    for mtb in mtbs:
        # get the properties file from server
        properties = mtb.zoomify_properties
        print(properties)
        try:
            url_response = urllib2.urlopen(properties)
            
            # now parse the document
            tree = ET.parse(url_response) 
            root = tree.getroot()
            root_attributes = root.attrib
            print "Width: %s, Height: %s"%(root_attributes['WIDTH'],root_attributes['HEIGHT'])
            
            # update db
            mtb.zoomify_width = root_attributes['WIDTH']
            mtb.zoomify_height = root_attributes['HEIGHT']
        except:
            pass
        
    dbsession.commit()  
if __name__ == '__main__':
    main()

