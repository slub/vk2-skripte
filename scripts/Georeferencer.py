#!/usr/bin/env python
#/******************************************************************************
# * $Id: Georefencer.py 2014-01-17 jmendt $
# *
# * Project:  Virtuelles Kartenforum 2.0
# * Purpose:  Script checking for validated georeferenceprocess and produce 
# *           corresponding results.
# * Author:   Jacob Mendt
# *
# *
# ******************************************************************************
# * Copyright (c) 2014, Jacob Mendt
# *
# * Permission is hereby granted, free of charge, to any person obtaining a
# * copy of this software and associated documentation files (the "Software"),
# * to deal in the Software without restriction, including without limitation
# * the rights to use, copy, modify, merge, publish, distribute, sublicense,
# * and/or sell copies of the Software, and to permit persons to whom the
# * Software is furnished to do so, subject to the following conditions:
# *
# * The above copyright notice and this permission notice shall be included
# * in all copies or substantial portions of the Software.
# *
# * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# * DEALINGS IN THE SOFTWARE.
# ****************************************************************************/

import sys, os, logging, argparse
from sqlalchemy.exc import IntegrityError

# set path of the project directory for finding the correct modules
sys.path.insert(0, os.path.abspath('..'))

from settings import sqlalchemy_engine, georef_settings
from src.models.Meta import initializeDb
from src.models.Georeferenzierungsprozess import Georeferenzierungsprozess
from src.models.Messtischblatt import Messtischblatt
from src.models.RefMtbLayer import RefMtbLayer
from src.csw.InsertMetadata import insertMetadata
from src.georef.georeferenceprocess import GeoreferenceProcessManager
from src.utils.Exceptions import GeoreferenceProcessNotFoundError, GeoreferenceProcessingError



def getGeoreferenceProcess(dbsession, logger):
    responseProcess = []
    try:
        logger.debug('Start searching for georeference process orders.')
        
        # does a matching
        for georefProc, mtb in dbsession.query(Georeferenzierungsprozess, Messtischblatt).\
                        filter(Georeferenzierungsprozess.messtischblattid == Messtischblatt.id).\
                        filter(Messtischblatt.isttransformiert == False).\
                        filter(Georeferenzierungsprozess.typevalidierung != 'waiting').\
                        all():
            
            print 'Georeference process'
            print 'Id: %s'%georefProc.id
            print 'MtbId: %s'%georefProc.messtischblattid
            print 'Timestamp: %s'%georefProc.timestamp
            print '===================='
            
            responseProcess.append((georefProc, mtb))
        
        if len(responseProcess) == 0:
            raise GeoreferenceProcessNotFoundError('No process for georeference available.')
            
        return responseProcess
    
    except GeoreferenceProcessNotFoundError:
        raise     
    except:
        logger.error('Error while searching for a georeference process order.')
        raise
    
def computeGeoreferenceResult(georeference_process, messtischblatt, dbsession, logger):
    logger.debug('Starting georeferencing for a zoomify picture of messtischblatt %s.'%messtischblatt.id)
    destFile = os.path.join(georef_settings['destination_dir'], messtischblatt.dateiname+'.tif')
    georef_process_manager = GeoreferenceProcessManager(dbsession, georef_settings['tmp_dir'], logger)
    response = georef_process_manager.__runStableGeoreferencing__(georeference_process, messtischblatt, georef_settings['tmp_dir'], destFile)
    if response == destFile:
        logger.debug('Processing of georeferencing result sucessfully.')
            
        print 'Respones path'
        print '============='
        print response 
            
        return response
    else:
        logger.debug('Processing of georeferencing result failed.')
        raise GeoreferenceProcessingError('Processing of georeferencing result failed.')
    
def updateDatabase(mtb_dest_path, messtischblatt, dbsession, logger):
    # update verzeichnispfad for messtischblatt
    messtischblatt.verzeichnispfad = mtb_dest_path
    messtischblatt.isttransformiert = True
        
    try: 
        # register new relation to layer
        refmtblayer = RefMtbLayer.by_id(georef_settings['reference_layer'], messtischblatt.id, dbsession)
        if not refmtblayer:
            refmtblayer = RefMtbLayer(layer=georef_settings['reference_layer'], messtischblatt=messtischblatt.id)
            dbsession.add(refmtblayer)
    except IntegrityError as e:
        logger.error('(IntegrityError) duplicate key value violates unique constraint "refmtblayer_pkey"')
        print '(IntegrityError) duplicate key value violates unique constraint "refmtblayer_pkey"'
        pass
     
    return messtischblatt
    
def registerGeoreferenceMesstischblatt(georeference_process, messtischblatt, dbsession, logger):
    ''' This functions run's a georeference process for a single messtischblatt. If it 
        succeeds it's update the status for the messtischblatt in the database and push's 
        it metadata record to the metadata catalog '''
    
    logger.info('Produce georeference result for messtischblatt with id %s ...'%messtischblatt.id)
    destPath = computeGeoreferenceResult(georeference_process, messtischblatt, dbsession, logger)
    
    logger.info('Georeference result successfully. Now Update database ...')
    updatedMesstischblatt = updateDatabase(destPath, messtischblatt, dbsession, logger)
    
    logger.info('Push data to metadata catalog ...')
    insertMetadata(id=messtischblatt.id,db=dbsession,logger=logger)
    
    logger.info('Registering of georeferenced messtischblatt with id %s finished.'%messtischblatt.id)
    return True

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    dbsession = initializeDb(sqlalchemy_engine)
    logger = logging.getLogger('sqlalchemy.engine')
   
    # parse command line
    parser = argparse.ArgumentParser(description='Parse the key/value pairs from the command line!')
    parser.add_argument('-modus', type=str, help='Run in testing or production modus')
    arguments = parser.parse_args()
    
    georefProcessQueue = None
    try:
        georefProcessQueue = getGeoreferenceProcess(dbsession, logger)
    except GeoreferenceProcessNotFoundError:
        pass
        print "There is no georeference process is process quene."   
           
    if arguments.modus == 'production' and georefProcessQueue:
        print 'Running script in modus "%s"'%arguments.modus
        for process in georefProcessQueue:
            if not process[1].isttransformiert:
                print 'Running georeference process with id %s for messtischblatt %s.'%(process[0].id,process[1].id)
                registerGeoreferenceMesstischblatt(georeference_process = process[0], 
                    messtischblatt = process[1], dbsession = dbsession, logger = logger)
                dbsession.flush()    
                print 'Georeference process %s was successful'%process[0].id
            print 'Georeference process %s for messtischblatt %s was already execute.'%(process[0].id,process[1].id) 

        dbsession.commit()
    elif georefProcessQueue:
        print 'Running script in modus "Testing"'
        georefNumber = 0
        for process in georefProcessQueue:            
            if not process[1].isttransformiert:
                print 'Running georeference process with id %s for messtischblatt %s.'%(process[0].id,process[1].id) 
                registerGeoreferenceMesstischblatt(georeference_process = process[0], 
                    messtischblatt = process[1], dbsession = dbsession, logger = logger)
                dbsession.flush()  
                print 'Georeference process %s was successful'%process[0].id
                georefNumber += 1
            print 'Georeference process %s for messtischblatt %s was already execute.'%(process[0].id,process[1].id) 
                
        print "Georef Number %s"%georefNumber