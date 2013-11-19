'''
Created on Nov 18, 2013

@author: mendt
'''
import unittest
from psycopg2 import IntegrityError
from datetime import datetime
from settings import params_database
from UpdateMappingServices import VrtDB, createUpdateProcess, UpdateProcess, getActualTimestamp, buildCmd_createShapeTileIndex, createVirtualDataset,getTimestampListForUpdate
from subprocess import CalledProcessError

class TestUpdateProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.database = VrtDB(params_database)
        cls.dummyTimestamp = 1901
        cls.dummyLayerId = 87
        cls.dummyVrtId = 100293
       
    def setUp(self):
        self.backupStatus = self.database.__executeSQLQuery__("SELECT lastupdate FROM virtualdatasets WHERE id = %s;",
                [self.dummyVrtId], 'SELECT')[0][0]
        self.dummyUpdateProcess = createUpdateProcess(self.dummyTimestamp, self.dummyLayerId, self.database)
   
    def tearDown(self):
        self.database.__executeSQLQuery__("UPDATE virtualdatasets SET lastupdate = %s WHERE id = %s;",
                [self.backupStatus, self.dummyUpdateProcess.id], 'WRITE')

    def testStatusPending(self):
        self.dummyUpdateProcess.__statusPending__()
        checkStatus = self.database.__executeSQLQuery__("SELECT lastupdate FROM virtualdatasets WHERE id = %s;", [100293], "SELECT")[0][0]
        self.assertEqual(checkStatus, 'PENDING', "Testing - __statusPending__  successful!")
        
    def testStatusUpdate(self):
        self.assertTrue(self.dummyUpdateProcess.__statusUpdated__())
        
    def testCreateUpdateProcess(self):
        self.assertIsNotNone(createUpdateProcess(1900, 87, self.database), "Testing - createUpdateProcess successful!")
        self.assertIsInstance(createUpdateProcess(1900, 87, self.database), UpdateProcess)
        
    def testCreateUpdateProcessFail(self):
        self.assertRaises(IntegrityError, createUpdateProcess, self.dummyTimestamp, self.dummyLayerId, self.database)
        
    def testUpdateDatabaseRel(self):
        self.assertTrue(self.dummyUpdateProcess.__updateDatabaseRel__())
        
    def testUpdateTimeCoverage(self):
        updateProcess = createUpdateProcess(1868, 87, self.database)
        self.assertIsNone(updateProcess.updateTimeCoverage())
        
class TestUtilsFunction(unittest.TestCase):
    
    def testBuildCmd_createShapeTileIndex(self):
        dummy_cmd = buildCmd_createShapeTileIndex(datetime(1901, 1, 1, 0, 0, 0), '/home/mendt/Documents/tmp/tmp/1901')
        print(dummy_cmd)
        self.assertIsInstance(dummy_cmd, str)
        
    def testGetActualTimestamp(self):
        timestamp = getActualTimestamp()
        self.assertIsInstance(timestamp , str)
    
    @unittest.skip('testCreateVirtualDataset')
    def testCreateVirtualDataset(self):
        target_path = createVirtualDataset(datetime(1901, 1, 1, 0, 0, 0))
        self.assertIsInstance(target_path, str)
    
    @unittest.skip('testCreateVirtualDatasetFail')
    def testCreateVirtualDatasetFail(self):
        self.assertRaises(CalledProcessError, createVirtualDataset, datetime(1991, 1, 1, 0, 0, 0))
        
    def testGetTimestampListForUpdate(self):
        dummyResponse = getTimestampListForUpdate(VrtDB(params_database))
        print(dummyResponse)
        self.assertIsInstance(dummyResponse, list)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()