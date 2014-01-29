'''
Created on Jan 28, 2014

@author: mendt
'''
import unittest, logging, sys, os

# set path of the project directory for finding the correct modules
parentPath = os.path.abspath('../..')
sys.path.insert(0, parentPath)
sys.path.append(os.path.abspath('.'))

from settings import sqlalchemy_engine, params_gdal, params_database
from src.models.Meta import initializeDb
from src.models.Virtualdatasets import Virtualdatasets
from src.utils.Utils import createLogger
from scripts.UpdateMappingService import getUpdateLayerTimestamps, UpdateProcess

class TestUpdateMappingService(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.logger = createLogger('sqlalchemy.engine', logging.DEBUG)
        cls.dbsession = initializeDb(sqlalchemy_engine)
        
    def test_getUpdateLayerTimestamps(self):
        response = getUpdateLayerTimestamps(self.dbsession, self.logger, 87)
        print "Response getUpdateLayerTimestamps - %s"%response
        self.assertTrue(isinstance(response, list), 'Function getUpdateLayerTimestamps - Failed because it is not a list.')
        
    def test_initUpdateProcess(self):
        response = UpdateProcess(self.dbsession, self.logger, Virtualdatasets.by_timestamp('1868-01-01 00:00:00', self.dbsession))
        print 'Response UpdateProcess Init - %s'%response
        self.assertTrue(isinstance(response, UpdateProcess), 'Constructor UpdateProcess - Failed because response is not a UpdateProcess object.')
    
    @unittest.skip('test_updateVrt_withoutCache')
    def test_updateVrt_withoutCache(self):
        
        print "=============================="
        print "The update vrt without cache ..."
        print "=============================="
        
        updateProcess = UpdateProcess(self.dbsession, self.logger, Virtualdatasets.by_timestamp('1899-01-01 00:00:00', self.dbsession))
        response = updateProcess.updateVrt(tmp_dir = params_gdal['tmp_dir'], target_dir = params_gdal['tmp_dir'], database_params = params_database)

    @unittest.skip('test_updateVrt_withCache')
    def test_updateVrt_withCache(self):
        
        print "=============================="
        print "The update vrt with cache ..."
        print "=============================="
        
        updateProcess = UpdateProcess(self.dbsession, self.logger, Virtualdatasets.by_timestamp('1868-01-01 00:00:00', self.dbsession))
        response = updateProcess.updateVrt(tmp_dir = params_gdal['tmp_dir'], target_dir = params_gdal['tmp_dir'], database_params = params_database, refresh_cache = True)        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestGeoreferencer.testName']
    unittest.main()