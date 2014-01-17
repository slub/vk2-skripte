'''
Created on Jan 16, 2014

@author: mendt
'''
import unittest
import logging
from settings import sqlalchemy_engine, georef_settings, gn_settings
from scripts.Georeferencer import getGeoreferenceProcess, computeGeoreferenceResult, updateDatabase, registerGeoreferenceMesstischblatt
from src.csw.CswTransactionBinding import gn_transaction_delete
from src.models.Meta import initializeDb
from src.models.Georeferenzierungsprozess import Georeferenzierungsprozess
from src.models.Messtischblatt import Messtischblatt
from src.models.RefMtbLayer import RefMtbLayer
from src.georef.georeferenceprocess import GeoreferenceProcessManager

class TestGeoreferencer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger('sqlalchemy.engine')
        cls.dbsession = initializeDb(sqlalchemy_engine)
    
    def getDummyGeorefProcess(self):
        dummyGeorefProcess = GeoreferenceProcessManager(self.dbsession, georef_settings['tmp_dir'], self.logger)
        georefprocess = dummyGeorefProcess.registerGeoreferenceProcess(71055048,
                    'harald', '675:7885,7403.5:7867.5,7389.5:1434,660.25:1459.5', True, 'user')
        return georefprocess.id  
        
    def deleteDummyGeorefProcess(self, georefid): 
        self.dbsession.execute("DELETE FROM georeferenzierungsprozess WHERE id = :georefid;", {'georefid':georefid})


    #@unittest.skip('testGetGeoreferenceProcess')          
    def testGetGeoreferenceProcess(self):
        try:
            georefid = self.getDummyGeorefProcess()
            response = getGeoreferenceProcess(self.dbsession, self.logger)
            self.assertIsNotNone(response, 'Function testGetGeoreferenceProcess - Response is None but not expected.')
            self.assertTrue(len(response) > 0, 'Function testGetGeoreferenceProcess - No response object.')
            self.assertTrue(isinstance(response[0][0], Georeferenzierungsprozess), \
                             'Function testGetGeoreferenceProcess - Expected a object from typ <Georeferenzierungsprozess>, but failed.')
            self.assertTrue(isinstance(response[0][1], Messtischblatt), \
                             'Function testGetGeoreferenceProcess - Expected a object from typ <Messtischblatt>, but failed.')
        except:
            raise
        finally:
            self.deleteDummyGeorefProcess(georefid)
        
    
    #@unittest.skip('testComputeGeoreferenceResult')                  
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
        
    #@unittest.skip('testUpdateDatabase')                  
    def testUpdateDatabase(self):
        try:
            # create dummy data
            mtb_dest_path = '/home/mendt/Documents/tmp/tmp/df_dk_0010001_4648_1938.tif'
            mtb = Messtischblatt.by_id(71055048, self.dbsession)
            mtb_verzeichnispfad = mtb.verzeichnispfad
            mtb_isttransformiert = mtb.isttransformiert
             
            response = updateDatabase(mtb_dest_path, mtb, self.dbsession, self.logger)
            self.assertIsNotNone(response, 'Function testUpdateDatabase - Response is None but not expected.')
            self.assertEqual(response.verzeichnispfad, mtb_dest_path, 'Function testUpdateDatabase - Expected a verzeichnispfad %s but failed.'% mtb_dest_path)
            self.assertEqual(response.isttransformiert, True, 'Function testUpdateDatabase - Expected a isttransformiert True but failed.')

        except:
            raise
        finally:
            # restore database status
            mtb.verzeichnispfad = mtb_verzeichnispfad
            mtb.isttransformiert = mtb_isttransformiert
    
    #@unittest.skip('testRegisterGeoreferenceMesstischblatt')          
    def testRegisterGeoreferenceMesstischblatt(self):
        try:
            # create dummy data
            mtb_dest_path = '/home/mendt/Documents/tmp/tmp/df_dk_0010001_4648_1938.tif'
            mtb = Messtischblatt.by_id(71055048, self.dbsession)
            mtb_verzeichnispfad = mtb.verzeichnispfad
            mtb_isttransformiert = mtb.isttransformiert
            
            # create dummy georeference process
            georefid = self.getDummyGeorefProcess()
            georefprocess = Georeferenzierungsprozess.by_id(georefid, self.dbsession)
            
            response = registerGeoreferenceMesstischblatt(georefprocess, mtb, self.dbsession, self.logger)
            self.assertTrue(response, 'Function testRegisterGeoreferenceMesstischblatt - Response is not True but expected.')
            
        except:
            raise
        finally:
            # restore database status
            mtb.verzeichnispfad = mtb_verzeichnispfad
            mtb.isttransformiert = mtb_isttransformiert
            
            # not necessary as long this is not persisted
            #refmtblayer = RefMtbLayer(layer=georef_settings['reference_layer'], messtischblatt=mtb.id)
            #self.dbsession.delete(refmtblayer)
                                 
            # remoce metadata record
            gn_transaction_delete(mtb.dateiname, gn_settings['gn_username'], gn_settings['gn_password'], self.logger)
            
            # remove dummy georef process 
            self.deleteDummyGeorefProcess(georefid)


            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestGeoreferencer.testName']
    unittest.main()