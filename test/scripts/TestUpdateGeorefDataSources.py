'''
Created on Mar 6, 2014

@author: mendt
'''
import unittest, logging
from settings import sqlalchemy_engine, georef_settings, gn_settings, params_gdal, params_database
from src.csw.CswTransactionBinding import gn_transaction_delete
from src.models.Meta import initializeDb
from src.models.Georeferenzierungsprozess import Georeferenzierungsprozess
from src.models.Messtischblatt import Messtischblatt
from src.models.Virtualdatasets import Virtualdatasets
from src.utils.Utils import createLogger
from src.utils.Exceptions import GeoreferenceProcessNotFoundError, GeoreferenceProcessingError 
from src.georef.georeferenceprocess import GeoreferenceProcessManager
from scripts.UpdateGeorefDataSources import getGeoreferenceProcessQueue, computeGeoreferenceResult, updateDatabase, updateVrt

class TestUpdateGeorefDataSources(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sqlalchemy_logger = createLogger('sqlalchemy.engine', logging.DEBUG)
        cls.logger = createLogger('TestUpdateGeorefDataSources', logging.DEBUG)
        cls.dbsession = initializeDb(sqlalchemy_engine)

    @classmethod
    def getDummyGeorefProcess(self):
        dummyGeorefProcess = GeoreferenceProcessManager(self.dbsession, georef_settings['tmp_dir'], self.logger)
        georefprocess = dummyGeorefProcess.registerGeoreferenceProcess(71055048,
                    'harald', '675:7885,7403.5:7867.5,7389.5:1434,660.25:1459.5', True, 'user')
        return georefprocess.id  
    
    @classmethod  
    def deleteDummyGeorefProcess(self, georefid): 
        self.dbsession.execute("DELETE FROM georeferenzierungsprozess WHERE id = :georefid;", {'georefid':georefid})
    
    @unittest.skip('testGetGeoreferenceProcessQueue')      
    def testGetGeoreferenceProcessQueue(self):
        try:
            georefid = self.getDummyGeorefProcess()
            response = getGeoreferenceProcessQueue(self.dbsession, self.logger)
            
            print "Response testGetGeoreferenceProcessQueue - %s"%response
            print response.keys()
            
            self.assertIsNotNone(response, 'Function getGeoreferenceProcessQueue - Response is None but not expected.')
            self.assertTrue(len(response) > 0, 'Function getGeoreferenceProcessQueue - No response object.')
            self.assertTrue(isinstance(response.keys(), list), 'Function getGeoreferenceProcessQueue - Response object is not a dictionary.')
        except Exception as e:
            self.assertTrue(isinstance(e, GeoreferenceProcessNotFoundError), 'Function testGetGeoreferenceProcess - \
                Doesn\'t return a GeoreferenceProcessNotFoundErrpr.')
            if not isinstance(e, GeoreferenceProcessNotFoundError):
                raise
        finally:
            self.deleteDummyGeorefProcess(georefid)
    
    @unittest.skip('testComputeGeoreferenceResult')                            
    def testComputeGeoreferenceResult(self):
        try:
            # create dummy georeference process
            georefid = self.getDummyGeorefProcess()
            georefprocess = Georeferenzierungsprozess.by_id(georefid, self.dbsession)
            mtb = Messtischblatt.by_id(georefprocess.messtischblattid, self.dbsession)
            response = computeGeoreferenceResult(georefprocess, mtb, self.dbsession, self.logger)
            
            self.assertIsNotNone(response, 'Function testComputeGeoreferenceResult - Response is None but not expected.')
            self.assertEqual(response, '/home/mendt/Documents/tmp/tmp/df_dk_0010001_4648_1938.tif', 
                'Function testComputeGeoreferenceResult - response is not like expected.')
        except:
            raise
        finally:
            self.deleteDummyGeorefProcess(georefid)
                   
    @unittest.skip('testUpdateDatabase')  
    def testUpdateDatabase(self):
        try:
            # create dummy data
            mtb_dest_path = '/home/mendt/Documents/tmp/tmp/df_dk_0010001_4648_1938.tif'
            mtb = Messtischblatt.by_id(71055048, self.dbsession)
            mtb_verzeichnispfad = mtb.verzeichnispfad
            mtb_isttransformiert = mtb.isttransformiert
             
            response = updateDatabase(mtb_dest_path, mtb, self.dbsession, self.logger)
            self.assertEqual(mtb.verzeichnispfad, mtb_dest_path, 'Function testUpdateDatabase - Expected a verzeichnispfad %s but failed.'% mtb_dest_path)
            self.assertEqual(mtb.isttransformiert, True, 'Function testUpdateDatabase - Expected a isttransformiert True but failed.')

        except:
            raise
        finally:
            # restore database status
            mtb.verzeichnispfad = mtb_verzeichnispfad
            mtb.isttransformiert = mtb_isttransformiert
            
    #@unittest.skip('test_updateVrt_withoutCache')
    def test_updateVrt_withoutCache(self):
        
        print "=============================="
        print "The update vrt without cache ..."
        print "=============================="

        response = updateVrt(database_params = params_database, logger = self.logger, dbsession = self.dbsession, 
                             vrt = Virtualdatasets.by_timestamp('1919-01-01 00:00:00', self.dbsession))
        
        print 'Response test_updateVrt_withoutCache - %s'%response

    #@unittest.skip('test_updateVrt_withCache')
    def test_updateVrt_withCache(self):
        
        print "=============================="
        print "The update vrt with cache ..."
        print "=============================="
        
        response = updateVrt(database_params = params_database, logger = self.logger, dbsession = self.dbsession, 
                             vrt = Virtualdatasets.by_timestamp('1919-01-01 00:00:00', self.dbsession), refresh_cache = True)
 


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()