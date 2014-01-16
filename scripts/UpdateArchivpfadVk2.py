# -*- coding: utf-8 -*- 
'''
Created on Oct 14, 2013

@author: mendt

This scripts test if the messtischblatt objects from the database have a repräsentation 
as a jpeg. 
'''
# import database stuff 
from sqlalchemy import create_engine
from utils.messtischblatt import initialize_sql, Messtischblatt
from sqlalchemy import update
from settings import sqlalchemy_engine
# import stuff for searching directory 
import os
import logging

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
    
def getMesstischblaetterAsColl(dbsession):
    collMtbs = []
    mtbs = Messtischblatt.all(dbsession)
    for mtb in mtbs:
        collMtbs.append(mtb)
    return collMtbs

def getJpgInfoForMesstischblaetter(search_dir, collMtbs):
    newColl = {}
    for file in os.listdir(search_dir):
        name = parseMtbName(file)
        if 'jpg' in file:
            newColl[name] = os.path.join(search_dir, file)
    return newColl
        
''' main function '''  
def main(search_dir):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

    
    # initialize the database with the models
    engine = create_engine(sqlalchemy_engine, encoding='utf8', echo=True)
    dbsession = initialize_sql(engine)
    
    # get a collection of all mtbs object
    collMtbs = getMesstischblaetterAsColl(dbsession)
    
    # search directory 
    collMtbsPath = getJpgInfoForMesstischblaetter(search_dir, collMtbs)
    
    # for handling the double cases
    for mtb in collMtbs:
        path = collMtbsPath[mtb.dateiname]
        query = 'UPDATE messtischblatt SET archivpfad_vk2 = :newpath, hasjpeg = TRUE, jpegpath = :jpegpath WHERE id = :mtbid;'
        dbsession.execute(query,{'mtbid':mtb.id,'newpath':path})

    dbsession.commit()
            
if __name__ == '__main__':
    search_dir = "/srv/vk/data_archiv/0010000"
    main(search_dir)

