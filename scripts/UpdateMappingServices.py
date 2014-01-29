#!/usr/bin/env python
# -*- coding: utf-8 -*-
#/******************************************************************************
# * $Id: UpdateMappingService.py 2014-01-28 jmendt $
# *
# * @deprecated: delete > new script is UpdateMappingService
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

import psycopg2.extras

import subprocess
import argparse
from psycopg2 import IntegrityError
from datetime import datetime
from settings import params_database, params_gdal, params_mtbs, params_mapcache
from subprocess import CalledProcessError

query_getUpdateLayerTimestamps = "SELECT * FROM (SELECT mtb.id, mtb.isttransformiert, zeit.datierung FROM messtischblatt as mtb, md_zeit as zeit \
            WHERE mtb.isttransformiert = TRUE AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text) as foo LEFT JOIN refmtblayer as ref ON ref.messtischblatt = foo.id \
            AND ref.layer = 87 WHERE ref.messtischblatt IS NULL"
            
class AbstractDB(object):

    def __init__(self, connectionParameter):
        type(self).connectionParameter = connectionParameter
        type(self).connection = psycopg2.connect(type(self).connectionParameter)
    
    def __del__(self):
        self.connection.close()  
           
    def __executeSQLQuery__(self, query=None, values=None, type=None):
        writeSuccess = False
        try:
            cur = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if query != None and (type == None or type == "SELECT"):
                cur.execute(query,(values))
                records = cur.fetchall()
                cur.close()
                return records
            # write support
            if type != None and type == "WRITE":
                cur.execute(query,values)
                cur.close()
                writeSuccess = True
                return True
        except:
            self.connection.rollback()
            raise
        finally:
            if writeSuccess:
                self.connection.commit()
            
    def __toString__(self):
        print(self.connectionParameter)
        
class VrtDB(AbstractDB):
    
    def __init__(self, params):
        AbstractDB.__init__(self, "dbname='%s' user='%s' host='%s' password='%s'"%(params['db'],
                    params['user'],params['host'],params['password']))       
    
    def getVrt(self, layerid, timestamp):
        query = "SELECT * FROM virtualdatasets WHERE layerid = %s AND timestamp = '%s-01-01 00:00:00';"
        values = [layerid, timestamp]
        return self.__executeSQLQuery__(query, values, 'SELECT')[0]
    
    def getUnregisteredMtbs(self, year, layerid):
        ''' Get alls messtischblaetter form database which are not already registered in the database table refmtblayer for
        the @param layerid and the @param year '''
        query = "SELECT * FROM (SELECT mtb.id, mtb.isttransformiert, zeit.datierung FROM messtischblatt as mtb, md_zeit as zeit WHERE zeit.datierung = %s \
            AND mtb.id = zeit.id AND zeit.typ::text = 'a5064' AND mtb.isttransformiert = TRUE) as foo LEFT JOIN refmtblayer as ref ON ref.messtischblatt = foo.id \
            AND ref.layer = %s WHERE ref.messtischblatt IS NULL"
        values = [year, layerid]
        return self.__executeSQLQuery__(query, values, 'SELECT')
    
    def createMtbLayerRel(self, mtbid, layerid):
        query = "INSERT INTO refmtblayer(layer, messtischblatt) VALUES(%s, %s);"
        values = [layerid, mtbid]
        return self.__executeSQLQuery__(query, values, 'WRITE')
    
    def updateBoundingboxVrt(self, vrtid, year):
        query = "UPDATE virtualdatasets SET boundingbox = ( SELECT st_setsrid(st_envelope(st_extent(boundingbox)),4314) \
            FROM (SELECT mtb.boundingbox as boundingbox FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
            AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.datierung = %s) as foo) WHERE id = %s;"
        values = [year, vrtid]
        return self.__executeSQLQuery__(query, values, 'WRITE')
    
    def setStatus_Pending(self, vrtid):
        query = "UPDATE virtualdatasets SET lastupdate = 'PENDING' WHERE id = %s;"
        values = [vrtid]
        self.__executeSQLQuery__(query, values, 'WRITE')
        return 'PENDING'
    
    def setStatus_Update(self, id, timestamp):
        query = "UPDATE virtualdatasets SET lastupdate = %s WHERE id = %s;"
        values = [timestamp, id]
        self.__executeSQLQuery__(query, values, 'WRITE')
        return timestamp
    
    def getTimestampsForUpdate(self):
        query = "SELECT * FROM (SELECT mtb.id, mtb.isttransformiert, zeit.datierung FROM messtischblatt as mtb, md_zeit as zeit \
            WHERE mtb.isttransformiert = TRUE AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text) as foo LEFT JOIN refmtblayer as ref ON ref.messtischblatt = foo.id \
            AND ref.layer = 87 WHERE ref.messtischblatt IS NULL"
        values = []
        return self.__executeSQLQuery__(query, values, 'SELECT') 

def getUpdateLayerTimestamps(dbsession, logger):   
    """ Looks in the database for which timestamps are new georeference messtischblätter available
    
    Args:
        dbsession (sqlalchemy.orm.session.Session): session object for querying the database
        logger (Logger)
    Returns:
        list of timestamps for which a new georeference messtischblätter available.
    """ 
    print "log"
#     dbResponse = 
#     timestampsForUpdates = []
#     for record in listOfUpdateRecords:
#         if not record['datierung'] in timestampsForUpdates:
#             timestampsForUpdates.append(record['datierung'])
#     return sorted(timestampsForUpdates, key = int)
       
class UpdateProcess(object):
    
    def __init__(self, *args, **kwargs):
        self.updateStatus = None
        self.__setattr__('database', kwargs['database'])
        self.__initTimestamp__(kwargs['layerid'], kwargs['timestamp'])
    
    def __initTimestamp__(self, layerid, timestamp):
        vrt_result = self.database.getVrt(layerid, timestamp)
        for key in vrt_result.keys():
            self.__setattr__(key, vrt_result[key])
        self.__raiseIfStatusIsPending__()    
        
    def __raiseIfStatusIsPending__(self):
        if self.lastupdate != 'PENDING':
            self.__statusPending__()
        elif self.lastupdate == 'PENDING':
            raise IntegrityError('A update process for this virtual datasets is already running!')
               
    def __updateDatabaseRel__(self):
        unregisteredMtbs = self.database.getUnregisteredMtbs(self.timestamp.year, params_mtbs['layerid'])
        
        for mtb in unregisteredMtbs:
            self.database.createMtbLayerRel(mtb['id'], params_mtbs['layerid'])
        return True
        
    def __statusPending__(self):
        self.__setattr__('status',self.database.setStatus_Pending(self.id))
    
    def __statusUpdated__(self):
        self.database.updateBoundingboxVrt(self.id, self.timestamp.year)
        self.status = self.database.setStatus_Update(self.id, getActualTimestamp()) 
        return True
    
    def __statusReset__(self):
        self.status = self.database.setStatus_Update(self.id, self.lastupdate)
                 
    def __del__(self):
        if not self.updateStatus:
            self.__statusReset__()

        
    def updateTimeCoverage(self):
        try:
            self.vrtPath = createVirtualDataset(self.timestamp)
            seedTimestamp(self.timestamp.year)
            self.__updateDatabaseRel__()
            self.updateStatus = self.__statusUpdated__()
            return self.updateStatus
        except CalledProcessError, e:
            pass



def createVirtualDataset(timestamp):
    shpTilePath = os.path.join(params_gdal['tmp_dir'], (str(timestamp.year)))
    targetVrtPath = os.path.join(params_gdal['target_dir'], '%s.vrt'%timestamp.year)

    # runs the commands via commandline
    try:
        runCommand(buildCmd_createShapeTileIndex(timestamp, shpTilePath))
        runCommand(buildCmd_createVrt(targetVrtPath,shpTilePath))
        runCommand(buildCmd_createVrtOverview(targetVrtPath))
        return targetVrtPath
    except CalledProcessError, e:
        print 'Subprocess.CalledProcessError while running: %s'%e.cmd
        print(e)
        raise
    except Exception, e:
        raise Exception("Error while creating virtual dataset!")      

def seedTimestamp(timestamp):
    ''' premise for that function is that a mapcache installation is configured properly '''
    command = "mapcache_seed -c /usr/share/mapcache/mapcache.xml -t 'messtischblaetter' \
            -M 5,5 -v -D TIME=%s -i \"level-by-level\" -f -n %s"%(timestamp,params_mapcache['threads'])
    try:
        print "Timestamp: %s"%timestamp
        runCommand(command)
    except:
        raise
    
def getActualTimestamp():
    return str(datetime.now())

def runCommand(command):
    print >> sys.stderr,"Running command '%s' ..."%command
    try:
        subprocess.check_call(command, shell=True)
        return True
    except:
        raise

def getTimestampListForUpdate(database):
    listOfUpdateRecords = database.getTimestampsForUpdate()
    timestampsForUpdates = []
    for record in listOfUpdateRecords:
        if not record['datierung'] in timestampsForUpdates:
            timestampsForUpdates.append(record['datierung'])
    return sorted(timestampsForUpdates, key = int)

def buildCmd_createShapeTileIndex(timestamp, shp_path):
    ''' @param timestamp - {datetime} 
        builds the terminal command for creating a shapefile which represents a tileindex for one timestamp'''  
    # The sql commands selects the geometry, the file path and the timestamps from messtischblaettern which are
    # already georeferenced  
    createShapeTileIndexCmd = "pgsql2shp -f %(shp_path)s -h %(host)s -u %(user)s -P '%(password)s' %(db)s \
        \"SELECT mtb.boundingbox, mtb.verzeichnispfad as location, zeit.time as time \
        FROM messtischblatt as mtb, md_zeit as zeit WHERE mtb.isttransformiert = True \
        AND mtb.id = zeit.id AND zeit.typ::text = 'a5064'::text AND zeit.time = '%(timestamp)s'\""         
    createShapeTileIndexCmd = createShapeTileIndexCmd % (dict({
        'shp_path': shp_path,                                  
        'timestamp': str(timestamp) }.items() + .items()))
    return createShapeTileIndexCmd

def buildCmd_createVrt(target_path, shapeTile_path):
    return "gdalbuildvrt -hidenodata -addalpha -overwrite -tileindex \"LOCATION\" %s %s"%(target_path, '%s.shp'%shapeTile_path)

def buildCmd_createVrtOverview(target_path):
    return "gdaladdo -ro -r average --config PHOTOMETRIC_OVERVIEW RGB --config TILED_OVERVIEW YES %s %s"%(target_path,params_gdal['overviewLevels'])

def createUpdateProcess(timestamp, layerid, database):
    return UpdateProcess(**{
        'database': database,
        'timestamp': timestamp,
        'layerid': layerid
})

def runUpdateProcess(timestamp, layerid, database):
    try:
        updateProcess = createUpdateProcess(timestamp, layerid, database)
        updateProcess.updateTimeCoverage()
    except IntegrityError,e :
        print(e)
        print('A update process for this virtual datasets is already running!')
        pass

      
def parseCommandLine():
    parser = argparse.ArgumentParser(description='Parse the key/value pairs from the command line!')
    parser.add_argument('-modus', type=str, help='Run update in full or reduced mode')
    return parser.parse_args()

        
if __name__ == '__main__':
    args = parseCommandLine()
    database = VrtDB(params_database)

    if args.modus == 'full':
        for timestamp in range(1868,1946):
            runUpdateProcess(timestamp, params_mtbs['layerid'], database)
    elif args.modus == 'reduced':
        toUpdatedTimestampList = getTimestampListForUpdate(database)
        for timestamp in toUpdatedTimestampList:
            runUpdateProcess(timestamp, params_mtbs['layerid'], database)