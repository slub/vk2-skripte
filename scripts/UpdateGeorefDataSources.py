#!/usr/bin/env python
# -*- coding: utf-8 -*-
#/******************************************************************************
# * $Id: UpdateMappingService.py 2014-01-28 jmendt $
# *
# * Project:  Virtuelles Kartenforum 2.0
# * Purpose:  This script encapsulate then tasks which are run for updating the vk2 mapping services. This 
# *           includes asking the database for new georeference process parameter and if they are available 
# *           it run's incremental for each timestamp the following process. At first it's calculate for all
# *           messtischblätter per timestamp the georeference maps. After that it recalculate the virtual    
# *           datasets for the timestamps, which are used for by the original wms for publishing the messtischblätter.
# *           After that it reseeds the cache for there extend of the new georeferenced messtischblätter for 
# *           the timestamp. At least it update's the database and pushed the metadata for the messtischblätter
# *           to the csw service. From this moment on the messtischblätter together with there metadata are 
# *           available for the users. 
# * Author:   Jacob Mendt
# * @todo:    Update georeference datasource
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
import logging, argparse, os, subprocess, sys
from datetime import datetime
from subprocess import CalledProcessError
from sqlalchemy.exc import IntegrityError

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, os.pardir))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from src.models.Meta import initializeDb
from src.models.Georeferenzierungsprozess import Georeferenzierungsprozess
from src.models.Messtischblatt import Messtischblatt
from src.models.MetadatenZeit import MetadatenZeit
from src.models.RefMtbLayer import RefMtbLayer
from src.models.Virtualdatasets import Virtualdatasets
from src.csw.InsertMetadata import insertMetadata
from src.georef.georeferenceprocess import GeoreferenceProcessManager
from src.utils.Utils import createLogger
from src.utils.Exceptions import GeoreferenceProcessNotFoundError, GeoreferenceProcessingError, MissingParameterException, WrongParameterException

""" Default options """
# Threads which the mapcache_seeder uses
SEEDER_NRTHREADS = 2 
# EPSG Code of the grid coordinate system from the cache
SEEDER_EPSG = 900913

# Directory for saving the temporary files
TMP_DIR = '/tmp'

# Target dir for georeference messtischblatt
GEOREF_TARGET_DIR = '/tmp'

# Target dir for saving the virtual datasets
VRT_TARGET_DIR = '/tmp'
# Overview levels for VRT (see gdaladdo)
VRT_OVERVIEW_LEVELS = '64 128 256 512'

# Database parameter for messtischblatt db
PARAMS_DATABASE = {
    'host':'localhost',
    'user':'postgres',
    'password':'postgres',
    'db':'messtischblattdb',    
}

# Id of the database layer where the messtischblatt should be registered
MTB_LAYER_ID = 87

""" Functions """
def getGeoreferenceProcessQueue(dbsession, logger):
    """ This function request the georeference processes together with the needed
        information from the database.
        
    Arguments:
        dbsession {sqlalchemy.orm.session.Session}
        logger (Logger)
    Returns:
        dictionary where the key is a timestamp and the value a list object containing 
        tuple which contain orm mapper for the tables georeferenzierungsprozess and
        messtischblatt """ 
    
    georef_queue = {}
    try:
        logger.debug('Generating georeference process queue ...')
        
        # Request all new georeference process parameter from the database, for 
        # messtischblätter which are not georeference yet.
        for georefProc, mtb in dbsession.query(Georeferenzierungsprozess, Messtischblatt).\
                        filter(Georeferenzierungsprozess.messtischblattid == Messtischblatt.id).\
                        filter(Messtischblatt.isttransformiert == False).\
                        filter(Georeferenzierungsprozess.typevalidierung != 'waiting').\
                        all():
            
            # request timestamp for the messtischblatt
            timestamp = MetadatenZeit.getRefTimeForMesstischblatt(mtb.id, dbsession).time.year
            
            logger.debug('Found georeference process with id {0} for messtischblatt {1} (time: {2}) from the date {3}'.format(georefProc.id,
                georefProc.messtischblattid, timestamp, georefProc.timestamp))
            
            # append to response
            if timestamp in georef_queue:
                georef_queue[timestamp].append((georefProc, mtb))
            else:
                georef_queue[timestamp] = [(georefProc, mtb)]
        
        # if no new georeference processes found raise error 
        if len(georef_queue) == 0:
            raise GeoreferenceProcessNotFoundError('No process for georeference available.')
            
        return georef_queue 
    except:
        logger.error('Unknown error while trying to accumulate georeference process information ...')
        raise
    

def buildCacheRestrictShapefile(time, shp_path, database_params):
    """ The created command uses pgsql2shp to compute a shapefile, which displays the
        spatial extend for which the cache should be updated. 
        
        Arguments:
            time {Integer} Number year
            shp_path {String}
            database_params {dict}
        Returns: {String} """
    cmd_template = "pgsql2shp -f %(shp_path)s -h %(host)s -u %(user)s -P '%(password)s' %(db)s \
        \"SELECT st_transform(mtb.boundingbox, %(target_epsg)s), zeit.time as time FROM messtischblatt as mtb, md_zeit as zeit WHERE \
        mtb.isttransformiert = True AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung = %(time)s\""  
    return cmd_template % (dict({
        'shp_path': shp_path,                                  
        'time': time,
        'target_epsg': SEEDER_EPSG,
    }.items() + database_params.items()))
    
def buildCreateShapeTileIndexCmd(timestamp, shp_path, database_params):
    """ Create the command for command line processing of a shapefile, which represents
        a tileindex for one timestamp for all historic messtischblaetter.
        
        Arguments:
            timestamp {Integer} Time in year
            shp_path {String}
            database_params {dict}
        Returns: {String} """    
    createShapeTileIndexCmd = "pgsql2shp -f %(shp_path)s -h %(host)s -u %(user)s -P '%(password)s' %(db)s \
    \"SELECT mtb.boundingbox, mtb.verzeichnispfad as location, zeit.time as time \
    FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
    AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung = %(timestamp)s\""             
    return createShapeTileIndexCmd % (dict({
        'shp_path': shp_path,                                  
        'timestamp': str(timestamp) 
    }.items() + database_params.items()))

def buildSeedingCmd(timestamp,  ogr_datasource):
    """ Create's a command for seeding the new vrt. Premise is preconfigured mapcache
        
        Arguments:
            timestamp {String}
            ogr_datasource {String} Path to ogr datasource
        Returns: {String} """
    return "mapcache_seed -c /usr/share/mapcache/mapcache.xml -t 'messtischblaetter' \
            -M 5,5 -v -D TIME=%s -i \"level-by-level\" -f -n %s -d \"%s\""%(timestamp,SEEDER_NRTHREADS,ogr_datasource)

def buildCreateVrtCmd(target_path, shapefile_path):
    """ Create the command for producing a virtutal dataset via gdalbuildvrt command on 
        the basic of a shapefile        
        
        Arguments:
            target_path {string}
            shapefile_path {string} Shapefile which represents the tileindex and has a attribute 'LOCATION'
        Returns: {string}
    """
    return "gdalbuildvrt --config GDAL_CACHEMAX 500 -hidenodata -addalpha -overwrite -tileindex \"LOCATION\" %s %s"%(target_path, '%s.shp'%shapefile_path)

def buildCreateVrtOverviewCmd(vrt_path):
    """ Creates the command for producing overviews for a vrt
        the basic of a shapefile
                
        Arguments:
            vrt_path {String}
        Returns {String} """
    return "gdaladdo --config GDAL_CACHEMAX 500 -ro -r average --config PHOTOMETRIC_OVERVIEW RGB --config TILED_OVERVIEW YES %s %s"%(vrt_path,VRT_OVERVIEW_LEVELS)

def getVirtualDatasetCreateCommands(time, database_params, with_cache = False):
    """ This function create a virtual dataset for the given parameters 
        
        Arguments:
            time {Integer}
            database_params {dict} for querying the database via pgsql2shp
            with_cache {Boolean} If true also a update cache command is created
        Returns: {list} commands for creating virtual datasets """
    shpTilePath = os.path.join(TMP_DIR, (str(time)))
    targetVrtPath = os.path.join(VRT_TARGET_DIR, '%s.vrt'%time)

    # collect commands 
    commands = []
    commands.append(buildCreateShapeTileIndexCmd(time, shpTilePath, database_params))
    commands.append(buildCreateVrtCmd(targetVrtPath, shpTilePath))
    commands.append(buildCreateVrtOverviewCmd(targetVrtPath))
    
    if with_cache:
        restrict_cache_shp = os.path.join(TMP_DIR, '%s_cache'%time)
        commands.append(buildCacheRestrictShapefile(time, restrict_cache_shp, database_params))
        commands.append(buildSeedingCmd(time, restrict_cache_shp + '.shp'))
    return commands
   
def computeGeoreferenceResult(georeference_process, messtischblatt, dbsession, logger):
    """ This function computes a persistent georeference result for a messtischblatt 
    
        Arguments:
            georeference_process {src.models.Georeferenzierungsprozess}
            messtischblatt {src.models.Messtischblatt}
            dbsession {sqlalchemy.orm.session.Session}
            logger {Logger} """
    logger.debug('Starting georeferencing for a zoomify picture of messtischblatt %s.'%messtischblatt.id)
    destFile = os.path.join(GEOREF_TARGET_DIR, messtischblatt.dateiname+'.tif')
    georef_process_manager = GeoreferenceProcessManager(dbsession, TMP_DIR, logger)
    response = georef_process_manager.__runStableGeoreferencing__(georeference_process, messtischblatt, TMP_DIR, destFile)
    if response == destFile:
        logger.debug('Processing of georeferencing result sucessfully.')
        return response
    else:
        logger.debug('Processing of georeferencing result failed.')
        raise GeoreferenceProcessingError('Processing of georeferencing result failed.')
    
def updateDatabase(mtb_dest_path, messtischblatt, dbsession, logger):
    """ This function update's the database after new georeference messtischblatt is computed
    
        Arguments:
            mtb_dest_path {String}
            messtischblatt {src.models.Messtischblatt}
            dbsession {sqlalchemy.orm.session.Session}
            logger {Logger} """
    try: 
        logger.info('Register georeference messtischblatt (%s) in database ...'%messtischblatt.id)

        # update verzeichnispfad for messtischblatt
        messtischblatt.verzeichnispfad = mtb_dest_path
        messtischblatt.isttransformiert = True 
        
        # register new relation to layer
        refmtblayer = RefMtbLayer.by_id(MTB_LAYER_ID, messtischblatt.id, dbsession)
        if not refmtblayer:
            refmtblayer = RefMtbLayer(layer=MTB_LAYER_ID, messtischblatt=messtischblatt.id)
            dbsession.add(refmtblayer)
        dbsession.flush()
    except IntegrityError as e:
        logger.error('(IntegrityError) duplicate key value violates unique constraint "refmtblayer_pkey"')
        pass

def updateVrt( database_params, refresh_cache = False, logger = None, dbsession = None, vrt = None):
    """ Processes a refreshed virtual dataset, updates the cache and after all update the 
        database relations in messtischblatt db
            
    Arguments:
        database_params (dict)
        refresh_cache (Boolean}: if set to true the cache is refreshed
        dbsession {sqlalchemy.orm.session.Session}
        logger {Logger}
        vrt {src.models.Virtualdataset} """
    try:
        logger.info('Starting updating virtual datasets for timestamp %s ...'%vrt.timestamp)
        commands = getVirtualDatasetCreateCommands(vrt.timestamp.year, database_params, refresh_cache)
    
        for command in commands:
            print command
        
        # now execute command
        for command in commands:
            logger.info('Execute - %s'%command)
            subprocess.check_call(command, shell = True)
            
        # now update database
        logger.info('Update database state for virtual datasets ...')
        # update boundingbox of virtual dataset
        query = "UPDATE virtualdatasets SET boundingbox = ( SELECT st_setsrid(st_envelope(st_extent(boundingbox)),4314) \
            FROM (SELECT mtb.boundingbox as boundingbox FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
            AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung = %s) as foo) WHERE id = %s;"
        dbsession.execute(query%(vrt.timestamp.year, vrt.id))
        # update last update timestamp
        vrt.lastupdate = str(datetime.now())
        dbsession.flush()
        
    except CalledProcessError as e:
        logger.error('CalledProcessErrro while trying to run a command for updating the virtual datasets.')
        raise
    except:
        raise
        
def processUpdateProcessForTimestamp(messtischblatt_process_queue, time, dbsession, logger):
    """ This function controls the complete update process for one timestamp 
        
    Arguments:
        messtischblatt_process_queue {list} containts tuple with the orm mapper for georeferenzierungsprozess and messtischblatt
        time {Integer}
        dbsession {sqlalchemy.orm.session.Session}
        logger {Logger}
          """ 
    logger.info('Run update process for timestamp %s ...'%time)
    
    # at first calculate georeference results for all messtischblätter and register them into the database 
    for tuple in messtischblatt_process_queue:
        georeference_process = tuple[0]
        messtischblatt = tuple[1]
        logger.info('Produce georeference result for messtischblatt with id %s ...'%messtischblatt.id)
        destPath = computeGeoreferenceResult(georeference_process, messtischblatt, dbsession, logger)
        updateDatabase(destPath, messtischblatt, dbsession, logger)
    
    # now update the virtual datasets and the cache backend
    vrt = Virtualdatasets.by_timestamp('1919-01-01 00:00:00', dbsession)
    updateVrt( PARAMS_DATABASE, refresh_cache = True, logger = logger, dbsession = dbsession, vrt = vrt)
    
    # push to catalog service
    for tuple in messtischblatt_process_queue:
        logger.info('Push metadata record for messtischblatt %s to cataloge service ...'%tuple[1])
        insertMetadata(id=tuple[1].id,db=dbsession,logger=logger)
    
    logger.info('Update process for timestamp %s finished.'%time)

""" Scritp Functions """
def scriptUpdateCacheMode(startTime, endTime, logger):
    """ This function makes a complete reseed of the cache for the given time range.
    
        Arguments:
            startTime {Integer}
            endTime {Integer}
            logger {Logger} """
    for time in range(startTime, endTime+1):
        cmd = "mapcache_seed -c /usr/share/mapcache/mapcache.xml -t 'messtischblaetter' \
            -M 5,5 -v -D TIME=%s -i \"level-by-level\" -f -n %s "%(time,SEEDER_NRTHREADS)
        logger.info('Reseed timestamp %s with command: %s'%(time, cmd))
        subprocess.check_call(cmd, shell = True)
    logger.info('Finish reseeding cache.')
    
def scriptProductionMode(arguments, logger):
    """ This function runs the script in production or testing mode
    
        Arguments:
            arguments {*args}
            logger {Logger} """
    logger.info('Initialize database connection ...')
    
    # init database
    sqlalchemy_enginge = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:5432/%(db)s'%(PARAMS_DATABASE)
    try:
        dbsession = initializeDb(sqlalchemy_enginge)
    except:
        logger.error('Could not initialize database. Plase check your database settings parameter.')
        raise WrongParameterException('Could not initialize database. Plase check your database settings parameter.')
    
    # get georeference jobs
    georefProcessQueue = None
    try:
        georefProcessQueue = getGeoreferenceProcessQueue(dbsession, logger)
    except GeoreferenceProcessNotFoundError:
        logger.info('There are no new georeference process founded.')
        pass 
    
    if arguments.mode == 'production' and georefProcessQueue:
        logger.info('Running script in production mode ...')
        for key in georefProcessQueue:
            processUpdateProcessForTimestamp(georefProcessQueue[key], key, dbsession, logger)
        dbsession.commit()
        logger.info('Finish running script in production mode')
    elif arguments.mode == 'testing':
        logger.info('Running script in testing mode ...')
        keys = georefProcessQueue.keys()
        processUpdateProcessForTimestamp(georefProcessQueue[keys[0]], keys[0], dbsession, logger)
        
        for key in georefProcessQueue:
            processUpdateProcessForTimestamp(georefProcessQueue[key], key, dbsession, logger)
        logger.info('Finish running script in production mode')  

""" Main """    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This scripts handles the updating of the datasources of the Virtuelles Kartenforum 2.0. It could \
        process persistent georeference mtbs, publish metadata records, update the virtual datasets and reseeding the cache. If wantet it could also be used \
        to reseed the hole cache.', prog = 'Script UpdateGeorefDataSources.py')
    
    # parse command line
    parser = argparse.ArgumentParser(description='Parse the key/value pairs from the command line!')
    parser.add_argument('--mode', type=str, help='Run in "production" or "update_cache" mode. Without mode parameter it run\'s in testing mode.')
    parser.add_argument('--host', help='host for messtischblattdb')
    parser.add_argument('--user', help='user for messtischblattdb')
    parser.add_argument('--password', help='password for messtischblattdb')
    parser.add_argument('--db', help='db name for messtischblattdb')
    parser.add_argument('--log_file', help='define a log file')
    parser.add_argument('--tmp_dir', default='/tmp', help='define directory for temporary files (default: /tmp')
    parser.add_argument('--vrt_dir', default='/tmp', help='define directory for vrt files (default: /tmp')
    parser.add_argument('--georef_dir', default='/tmp', help='define directory for georeference messtischblatt files (default: /tmp')
    parser.add_argument('--seeder_threads', default=2, help='Number of threads the seeder utility should use (default: 2')  
    parser.add_argument('--with_cache', default=False, help='update cache (default: False)')
    parser.add_argument('--layerid', default=87, help='database layer id, which represents the vrt time layer (default: 87)')
    parser.add_argument('--time_range', type=str, default='1868/1945', help='Should be in the form "1868/1945". Works in collaboration with mode "update_cache" and describe\'s the time range, for which the cache should be updated.')
    arguments = parser.parse_args()
    
    # create logger
    if arguments.log_file:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sqlalchemy_logger = createLogger('sqlalchemy.engine', logging.DEBUG, logFile=''.join(arguments.log_file), formatter=formatter)     
        logger = createLogger('UpdateGeorefDataSources', logging.DEBUG, logFile=''.join(arguments.log_file), formatter=formatter)
    else: 
        sqlalchemy_logger = createLogger('sqlalchemy.engine', logging.WARN)
        logger = createLogger('UpdateGeorefDataSources', logging.DEBUG)   

    # parse parameter parameters
    if arguments.host:
        PARAMS_DATABASE['host'] = arguments.host
    if arguments.user:
        PARAMS_DATABASE['user'] = arguments.user
    if arguments.password:
        PARAMS_DATABASE['password'] = arguments.password
    if arguments.db:
        PARAMS_DATABASE['db'] = arguments.db
    if arguments.tmp_dir:
        TMP_DIR = arguments.tmp_dir
    if arguments.vrt_dir:
        VRT_TARGET_DIR = arguments.vrt_dir
    if arguments.georef_dir:
        GEOREF_TARGET_DIR = arguments.georef_dir
    if arguments.seeder_threads:
        SEEDER_NRTHREADS = arguments.seeder_threads
    if arguments.layerid:
        MTB_LAYER_ID = arguments.layerid    

    # if mode 'update_cache' than simply update cache
    if arguments.mode == 'update_cache':
        timerange_str = arguments.time_range.split('/')
        scriptUpdateCacheMode(int(timerange_str[0]), int(timerange_str[1]), logger)
    else:
        scriptProductionMode(arguments, logger)
        
