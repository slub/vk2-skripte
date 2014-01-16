#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@author: mendt
'''
import logging, shutil, sys, tempfile, uuid, os
from datetime import datetime
from settings import sqlalchemy_engine
from settings import templates, gn_settings
from src.csw.ChildMetadataBinding import ChildMetadataBinding
from src.csw.CswTransactionBinding import gn_transaction_insert, gn_transaction_delete
from src.models.Meta import initializeDb
from src.models.Messtischblatt import Messtischblatt
from src.models.MetadatenCore import MetadatenCore
from src.models.MetadatenZeit import MetadatenZeit
from src.models.MetadatenDatensatz import MetadatenDatensatz

def insertMetadata(id, db, logger):
    logger.debug('Start inserting metadata')
    try:
        tmpDirectory = tempfile.mkdtemp('', 'tmp_', templates['tmp_dir'])
        mdFile = createTemporaryCopy(templates['child'], tmpDirectory)
        metadata = getMetadataForMesstischblatt(id, db, logger)
        updateMetadata(mdFile, metadata, logger)   
        response = gn_transaction_insert(mdFile,gn_settings['gn_username'], gn_settings['gn_password'], logger)
        if '<csw:totalInserted>1</csw:totalInserted>' in response:
            return response
        else:
            logger.error('Problems while inserting metadata for messtischblatt id %s'%id)
            
            print "RESPONSE"
            print "========"
            print response
            
            return False
    except:
        raise
    finally:
        shutil.rmtree(tmpDirectory)

def createTemporaryCopy(srcFile, destDir, ending='xml'):
    try:
        destFile = os.path.join(destDir, str(uuid.uuid4()) + '.' + ending)
        shutil.copyfile(srcFile, destFile)
        return destFile
    except:
        raise
    
def getMetadataForMesstischblatt(id, db, logger):
    try:
        logger.debug('Start collection metadata information')
        mtb = Messtischblatt.by_id(id, db)
        metadata_core = MetadatenCore.by_id(id, db)
        metadata_time = MetadatenZeit.getRefTimeForMesstischblatt(id, db)
        metadata_dataset = MetadatenDatensatz.by_id(id, db)
        
        logger.debug('Metadata collection finish. Creating response')
        metadata = {
                    'westBoundLongitude':str(mtb.BoundingBoxObj.llc.x),
                    'eastBoundLongitude':str(mtb.BoundingBoxObj.urc.x),
                    'southBoundLatitude':str(mtb.BoundingBoxObj.llc.y),
                    'northBoundLatitude':str(mtb.BoundingBoxObj.urc.y),
                    'identifier':mtb.dateiname,
                    'dateStamp': datetime.now().isoformat(' '),
                    'title': metadata_core.titel,
                    'cite_date': str(metadata_time.datierung),
                    'abstract': metadata_core.beschreibung,
                    'temporalExtent_begin': '%s-01-01'%metadata_time.datierung,
                    'temporalExtent_end': '%s-12-31'%metadata_time.datierung,
                    'permalink': metadata_dataset.permalink, 
                    'hierarchylevel': 'Messtischblatt' if mtb.mdtype == 'M' else 'Äquidistantenkarte' 
        }
        return metadata
    except:
        logger.error('Problems while trying to collect the metadata for the messtischblatt with id %s'%id)
        raise

def updateMetadata(file, metadata, logger):
    try:
        logger.debug('Start updating the metadata in the xml file %s'%file)
        mdEditor = ChildMetadataBinding(file, logger)
        mdEditor.updateId(metadata['identifier'])
        mdEditor.updateTitle(metadata['title'])
        mdEditor.updateAbstract(metadata['abstract'])
        mdEditor.updateHierarchyLevelName(metadata['hierarchylevel'])
        mdEditor.updateBoundingBox(metadata['westBoundLongitude'], metadata['eastBoundLongitude'], 
                                   metadata['southBoundLatitude'], metadata['northBoundLatitude'])
        mdEditor.updatePermalink(metadata['permalink'])
        mdEditor.updateDateStamp(metadata['dateStamp'])
        mdEditor.updateReferenceTime(metadata['temporalExtent_begin'], metadata['temporalExtent_end'])
        mdEditor.updateReferenceDate(metadata['cite_date'])
        mdEditor.saveFile(file)
        return True
    except:
        logger.error('Problems while updating the metadata for the xml file %s'%file)
        raise




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    dbSession = initializeDb(sqlalchemy_engine)
    logger = logging.getLogger('sqlalchemy.engine')
    
    # get all messtischblätter
    messtischblaetter = Messtischblatt.all(dbSession)
    for messtischblatt in messtischblaetter:
        if messtischblatt.isttransformiert:
            #response = gn_transaction_delete(messtischblatt.dateiname, gn_settings['gn_username'], gn_settings['gn_password'], logger)
            response = insertMetadata(id=messtischblatt.id,db=dbSession,logger=logger)
            print "Response - delete record"
            print "========================"
            print response
            