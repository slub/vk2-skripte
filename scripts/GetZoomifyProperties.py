# -*- coding: utf-8 -*- 
'''
Created on Oct 14, 2013

@author: mendt

This scripts fetch the zoomify properties file from url and parse the width height
'''
import logging, urllib2
import xml.etree.ElementTree as ET

from settings import sqlalchemy_engine
from src.utils.Utils import createLogger
from src.models.Meta import initializeDb
from src.models.Messtischblatt import Messtischblatt





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
    # initialize the database with the models
    logger = createLogger('sqlalchemy.engine', logging.DEBUG)
    dbsession = initializeDb(sqlalchemy_engine)
    
    # get a collection of all mtbs object
    mtbs = Messtischblatt.all(dbsession)
    for mtb in mtbs:
        if mtb.zoomify_height == None and mtb.zoomify_width == None:
            # get the properties file from server
            properties = mtb.zoomify_properties
            logger.info(properties)
            try:
                url_response = urllib2.urlopen(properties)
                
                # now parse the document
                tree = ET.parse(url_response) 
                root = tree.getroot()
                root_attributes = root.attrib
                logger.info("Width: %s, Height: %s"%(root_attributes['WIDTH'],root_attributes['HEIGHT']))
                
                # update db
                mtb.zoomify_width = root_attributes['WIDTH']
                mtb.zoomify_height = root_attributes['HEIGHT']
            except:
                pass
        
    dbsession.commit() 
     
if __name__ == '__main__':
    main()

