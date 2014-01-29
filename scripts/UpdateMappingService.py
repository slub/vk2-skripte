#!/usr/bin/env python
# -*- coding: utf-8 -*-
#/******************************************************************************
# * $Id: UpdateMappingService.py 2014-01-28 jmendt $
# *
# * Project:  Virtuelles Kartenforum 2.0
# * Purpose:  This script encapsulate then tasks which are run for updating the vk2 mapping services. 
# *           This tasks comprises the update of the web mapping service layer  time_idx (a postgis / virtual 
# *           dataset - time / tile index) by updating the virtual datasets and the equivalent database table 
# *           "virtualdatasets" . After that a seeding process for updating the tile cache is run. After the 
# *           cache is updated the database table "relmtblayer" is updated, so that the wfs layer which represents
# *           the single messtischblatt data is updated consistent to the viewing data. Before finishing the 
# *           updating for one timestamp the update data get registered in the database table "virtualdatasets" 
# *           by insert the update timestamp in the column "lastupdate".
# * Author:   Jacob Mendt
# * @todo:    Update boundingbox of virutal dataset
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
# ****************************************************************************/'''
import os, sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('.'))

import subprocess, argparse, logging
from subprocess import CalledProcessError
from datetime import datetime
from sqlalchemy.orm.session import Session

# own librarys 
from src.models.Meta import initializeDb
from src.models.Virtualdatasets import Virtualdatasets
from src.utils.Utils import createLogger
from src.models.RefMtbLayer import RefMtbLayer

query_getUpdateLayerTimestamps = "SELECT * FROM (SELECT mtb.id, mtb.isttransformiert, zeit.datierung FROM messtischblatt as mtb, md_zeit as zeit \
WHERE mtb.isttransformiert = TRUE AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung < 1945) as foo LEFT JOIN refmtblayer \
as ref ON ref.messtischblatt = foo.id AND ref.layer = %s WHERE ref.messtischblatt IS NULL"

query_getUnregisteredMtbsForTimestamp = "SELECT * FROM (SELECT mtb.id, mtb.isttransformiert, zeit.datierung FROM messtischblatt as mtb, md_zeit as zeit \
WHERE mtb.isttransformiert = TRUE AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung < 1945 AND zeit.datierung = %s) as foo \
LEFT JOIN refmtblayer as ref ON ref.messtischblatt = foo.id AND ref.layer = %s WHERE ref.messtischblatt IS NULL"

query_updateVrtBoundingBox = "UPDATE virtualdatasets SET boundingbox = ( SELECT st_setsrid(st_envelope(st_extent(boundingbox)),4314) \
FROM (SELECT mtb.boundingbox as boundingbox FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung = %s) as foo) WHERE id = %s;"

def buildCreateShapeTileIndexCmd(timestamp, shp_path, database_params):
    """ Create the command for command line processing of a shapefile, which represents
        a tileindex for one timestamp for all historic messtischblaetter.
        
        Args:
            timestamp (string): as year
            shp_path (string): path
            database_params {dict}
        Returns:
            command (string)
    """
    
    createShapeTileIndexCmd = "pgsql2shp -f %(shp_path)s -h %(host)s -u %(user)s -P '%(password)s' %(db)s \
    \"SELECT mtb.boundingbox, mtb.verzeichnispfad as location, zeit.time as time \
    FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
    AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.time = '%(timestamp)s'\""      
       
    createShapeTileIndexCmd = createShapeTileIndexCmd % (dict({
        'shp_path': shp_path,                                  
        'timestamp': str(timestamp) }.items() + database_params.items()))
    return createShapeTileIndexCmd

def buildSeedingCmd(timestamp, threads):
    """ Create's a command for seeding the new vrt. Premise is preconfigured mapcache
        
        Args:
            timestamp (string)
            threads (int)
        Returns:
            command (string)
    """
    ''' premise for that function is that a mapcache installation is configured properly '''
    command = "mapcache_seed -c /usr/share/mapcache/mapcache.xml -t 'messtischblaetter' \
            -M 5,5 -v -D TIME=%s -i \"level-by-level\" -f -n %s"%(timestamp,threads)
    return command

def buildCreateVrtCmd(target_path, shapefile_path):
    """ Create the command for producing a virtutal dataset via gdalbuildvrt command on 
        the basic of a shapefile        
        Args:
            target_path (string):
            shapefile_path (string): shapefile which represents the tileindex and has a attribute 'LOCATION'
        Returns:
            command (string)
    """
    return "gdalbuildvrt --config GDAL_CACHEMAX 500 -hidenodata -addalpha -overwrite -tileindex \"LOCATION\" %s %s"%(target_path, '%s.shp'%shapefile_path)

def buildCreateVrtOverviewCmd(vrt_path, overview_levels):
    """ Creates the command for producing overviews for a vrt
        the basic of a shapefile        
        Args:
            vrt_path (string)
            overview_levels (string): '64 128 256 512'
        Returns:
            command (string)
    """
    return "gdaladdo --config GDAL_CACHEMAX 500 -ro -r average --config PHOTOMETRIC_OVERVIEW RGB --config TILED_OVERVIEW YES %s %s"%(vrt_path,overview_levels)

def getUpdateLayerTimestamps(dbsession, logger, layerid):   
    """ Looks in the database for which timestamps are new georeference messtischblätter available
    
    Args:
        dbsession (sqlalchemy.orm.session.Session): session object for querying the database
        logger (Logger)
    Returns:
        list of timestamps for which a new georeference messtischblätter available.
    """ 
    logger.debug('Trying to query timestamps for georeferen messtischblaetter from database.')
    try:
        timestamps = []
        query = query_getUpdateLayerTimestamps%layerid
        databaseResponse = dbsession.execute(query)
        for record in databaseResponse:
            if not record['datierung'] in timestamps:
                timestamps.append(record['datierung'])
        return sorted(timestamps, key = int)
    except Exception as e:
        logger.error('Failed to derive timestamps for georeferen messtischblaetter from database')
        logger.error(e)
        raise

def getVirtualDatasetCreateCommands(timestamp, tmp_dir, target_dir, database_params, overview_levels):
    """ This function create a virtual dataset for the given parameters 
        
        Args:
            timestamp (sqlalchemy.DateTime)
            tmp_dir (string): path
            target_dir (string): path 
            database_params (dict): for querying the database via pgsql2shp
            overview_levels (string): '64 128 256 512'
        Returns:
            list: commands for creating virtual datasets
    """
    shpTilePath = os.path.join(tmp_dir, (str(timestamp.year)))
    targetVrtPath = os.path.join(target_dir, '%s.vrt'%timestamp.year)

    # collect commands 
    commands = []
    commands.append(buildCreateShapeTileIndexCmd(timestamp, shpTilePath, database_params))
    commands.append(buildCreateVrtCmd(targetVrtPath, shpTilePath))
    commands.append(buildCreateVrtOverviewCmd(targetVrtPath, overview_levels))
    return commands

class UpdateProcess(object):
    """ The class encapsulate the process organization for processing a new vrt for one timestamp
        and also refresh the cache. It marks running processes in the database as 'PENDING'. If
        the process crashes it resets the database to the earlier state. """
        
    def __init__(self, dbsession, logger, vrt):
        logger.debug('Initialize a UpdateProcess object for the virtual dataset %s.'%vrt.path)
        self.dbsession = dbsession
        self.logger = logger
        self.vrt = vrt
        self.updateProcessRunning = False

    def __del__(self):
        self.logger.debug('Delete update process for VRT %s'%self.vrt.id)
        if self.updateProcessRunning:
            self.__resetVrtStatus__()
                  
    def __executeCmd__(self, command):
        try:
            self.logger.info('Running command: %s'%command)
            subprocess.check_call(command, shell = True)
        except CalledProcessError as e:
            self.logger.error('CalledProcessError while running commnand %s'%command)
            self.logger.error(e)
            raise
        except:
            self.logger.error('Unknown error while running commnand %s'%command)
            raise
        
    def __setVrtStatusPending__(self):
        self.logger.debug('Update Process for VRT %s - set status \'PENDING\''%self.vrt.id)
        self.updateProcessRunning = True
        self.old_vrtstatus = self.vrt.lastupdate
        self.vrt.lastupdate = 'PENDING'
        self.dbsession.flush()
        
    def __setVrtNewLastUpdate__(self, status):
        self.logger.debug('Update Process for VRT %s - set status \'%s\''%(self.vrt.id, status))
        self.vrt.lastupdate = status
        self.dbsession.flush()
        
    def __resetVrtStatus__(self):
        self.logger.debug('Update process for VRT %s - Reset status to %s'%(self.vrt.id, self.old_vrtstatus))
        if not self.old_vrtstatus:
            self.vrt.lastupdate = self.old_vrtstatus
            self.dbsession.flush()
    

    def __updateDb__(self, time_as_year, layerid):
        """ This functions register all newly transformed messtischblätter in the database table relmtbvrt. 
        
            Args:
                time_as_year (int): year number
                layerid (int)
        """
        self.logger.info('Update database messtischblattdb ...')
        
        try:
            self.logger.debug('Update table refmtblayer ...')
            query = query_getUnregisteredMtbsForTimestamp % (time_as_year, layerid)
            unregisteredMtbs = self.dbsession.execute(query)
            for record in unregisteredMtbs:
                refmtblayer = RefMtbLayer(layer = layerid, messtischblatt = record['id'])
                self.dbsession.add(refmtblayer)
            
            self.logger.debug('Update boundingbox of vrt ...')
            query = query_updateVrtBoundingBox % (time_as_year, self.vrt.id)
            self.dbsession.execute(query)
            self.dbsession.flush()
        except:
            self.logger.error('Unknown error while trying to update the database ...')
            raise            
            
    def updateVrt(self, tmp_dir, target_dir, database_params, refresh_cache = False, nr_threads = 2, overview_levels = '64 128 256 512', layerid = 87):
        """ Processes a refreshed virtual dataset, updates the cache and after all update the 
            database relations in messtischblatt db
            
            Args:
                tmp_dir (String): path
                target_dir (String): path
                database_params (dict)
                refresh_cache (Boolean}: if set to true the cache is refreshed
                nr_threads (Int): number of threads used for cache
                overview_levels (string)
                layerid (Int): id for the layer which should be updated
        """
        
        self.logger.info('Starting update process for VRT %s ...'%self.vrt.id)
        try:
            self.__setVrtStatusPending__()
            
            self.logger.debug('Generate commands for creating virtual datasets')
            commands = getVirtualDatasetCreateCommands(self.vrt.timestamp, tmp_dir, target_dir, database_params, overview_levels)
            
            if refresh_cache:
                commands.append(buildSeedingCmd(self.vrt.timestamp.year, nr_threads))
            
            self.logger.debug('Starting exectuing of commands ...')
            for command in commands:
                self.__executeCmd__(command)
                
            self.logger.debug('Updating database ...')
            self.__updateDb__(self.vrt.timestamp.year, layerid)
            self.__setVrtNewLastUpdate__(str(datetime.now()))
        except:
            self.__resetVrtStatus__()

class WrongParameterException(Exception):
    """ Raised if there are missing parameters
        
        Attributes:
            msg  -- explanation of the error
    """
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)    
    
def runScript(args, logger):

    print "" # for better reading on the console
    
    testing = False
    if str(args.testing).upper() == 'TRUE':
        logger.info('Starting updating script for the mapping service of the "Virtuelles Kartenforum 2.0" in testing mode.')
        testing = True
    else:
        logger.info('Starting updating script for the mapping service of the "Virtuelles Kartenforum 2.0".')
     

    
    database_params = {'user':args.user, 'password':args.password,'host':args.host,'db':args.db}
    sqlalchemy_enginge = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:5432/%(db)s'%(database_params)
    dbsession = initializeDb(sqlalchemy_enginge)
    if not (isinstance(dbsession, Session)):
        logger.error('Failed initialize database with engine: %s'%sqlalchemy_enginge)
        raise WrongParameterException('Could not initialize database. Please check your database settings.')

    logger.info('Searching for update jobs ...')
    if str(args.mode).lower() == 'slim':
        logger.info('Run update process in slim mode.')
        jobs_list = getUpdateLayerTimestamps(dbsession, logger, args.layerid)
    else:
        logger.info('Run update process in full mode.')
        jobs_list = range(1868,1946)
    
    if str(args.with_cache).upper() == 'TRUE':
        logger.info('Updating mapping service with cache ...')
        for job in jobs_list:
            vrt = Virtualdatasets.by_timestamp('%s-01-01 00:00:00'%job, dbsession)
            updateProcess = UpdateProcess(dbsession, logger, vrt)
            updateProcess.updateVrt(tmp_dir = args.tmp_dir, target_dir = args.target_dir, database_params = database_params, refresh_cache = True)
            
    else:
        logger.info('Updating mapping service without cache ...')
        for job in jobs_list:
            vrt = Virtualdatasets.by_timestamp('%s-01-01 00:00:00'%job, dbsession)
            updateProcess = UpdateProcess(dbsession, logger, vrt)
            updateProcess.updateVrt(tmp_dir = args.tmp_dir, target_dir = args.target_dir, database_params = database_params)

    if not testing:
        logger.info('Commit changes to database ...')
        dbsession.commit()

if __name__ == '__main__':
    # argument parser for giving parameters to the script
    parser = argparse.ArgumentParser(description = 'This scripts creates / updates the virtualdatasets, the cache and the database\
     (relmtblayer/ boundingbox of vrt) for the mapping services of the "Virtuelles Kartenforum 2.0".', prog = 'Script UpdateMappingService.py')
    
    # add arguments  
    parser.add_argument('target_dir', help='define target directory for virtual datasets')
    parser.add_argument('--host', help='host for messtischblattdb')
    parser.add_argument('--user', help='user for messtischblattdb')
    parser.add_argument('--password', help='password for messtischblattdb')
    parser.add_argument('--db', help='db name for messtischblattdb')
    parser.add_argument('--log_file', help='define a log file')
    parser.add_argument('--tmp_dir', default='/tmp', help='define directory for temporary files (default: /tmp')
    parser.add_argument('--with_cache', default=False, help='update cache (default: False)')
    parser.add_argument('--layerid', default=87, help='database layer id, which represents the vrt time layer (default: 87)')
    parser.add_argument('--mode', default='full', help='Run update process in "full" or in "slim" mode. In "slim" mode it \
    looks for changes in the database and only update this timestamps. In "full" mode in update all timestamps. (default: "full")')
    parser.add_argument('--testing', help='Run update process in testing mode. That means changes will not be persist in the database. Be careful with this settings.')
    args = parser.parse_args()
    
    # create logger
    if args.log_file:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = createLogger('sqlalchemy.engine', logging.DEBUG, logFile=''.join(args.log_file), formatter=formatter)     
    else: 
        logger = createLogger('sqlalchemy.engine', logging.DEBUG)
    
    # run script
    try:
        runScript(args, logger)
    except WrongParameterException, e:
        logger.error(e.msg)
    

    


