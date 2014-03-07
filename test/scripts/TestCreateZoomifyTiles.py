'''
Created on Feb 24, 2014

@author: mendt
'''
import unittest, logging
from src.utils.Utils import createLogger
from scripts.CreateZoomifyTiles import parseXYSize, calculateTierSize, calculateTileCountUpToTier, createTiles, sortTileToTileGroups

class TestCreateZoomifyTiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logger = createLogger('Zoomify', logging.DEBUG)
        cls.testCase1 = {'path':'/home/mendt/Documents/tmp/df_dk_0010001_0294.tif','x':8911.0,'y':9545.0}
        cls.testCase2 = {'path':'/home/mendt/Documents/tmp/df_dk_0010001_0194.tif','x':8898.0,'y':9438.0}
        cls.testCase3 = {'path':'/home/mendt/Documents/tmp/df_dk_0010001_0193.tif','x':8352.0,'y':9462.0}
        
    def testParseXYSize(self):
        testResponse1 = parseXYSize(self.testCase1['path'])
        self.assertEqual(testResponse1['x'], self.testCase1['x'], 'X is not equal for response of test case 1.')
        self.assertEqual(testResponse1['y'], self.testCase1['y'], 'Y is not equal for response of test case 1.')
        
        testResponse2 = parseXYSize(self.testCase2['path'])
        self.assertEqual(testResponse2['x'], self.testCase2['x'], 'X is not equal for response of test case 2.')
        self.assertEqual(testResponse2['y'], self.testCase2['y'], 'Y is not equal for response of test case 2.')
        
        testResponse3 = parseXYSize(self.testCase3['path'])
        self.assertEqual(testResponse3['x'], self.testCase3['x'], 'X is not equal for response of test case 3.')
        self.assertEqual(testResponse3['y'], self.testCase3['y'], 'Y is not equal for response of test case 3.')

    def testCalculateTierSize(self):
        testResponse = calculateTierSize(self.testCase1['x'],self.testCase1['y'])
        self.logger.debug('Response calculateTierSize: %s'%testResponse)
        self.assertIsNotNone(testResponse, 'Response for calculateTierSize in None.')
        self.assertEqual(testResponse[-1], [1.0, 1.0], 'Response for calculateTierSize is not like expected.')
        
        testResponse2 = calculateTierSize(self.testCase2['x'],self.testCase2['y'])
        self.logger.debug('Response calculateTierSize: %s'%testResponse2)
        self.assertIsNotNone(testResponse2, 'Response for calculateTierSize in None.')
        self.assertEqual(testResponse2[-1], [1.0, 1.0], 'Response for calculateTierSize is not like expected.')        
        
        testResponse3 = calculateTierSize(self.testCase3['x'],self.testCase3['y'])
        self.logger.debug('Response calculateTierSize: %s'%testResponse3)
        self.assertIsNotNone(testResponse3, 'Response for calculateTierSize in None.')
        self.assertEqual(testResponse3[-1], [1.0, 1.0], 'Response for calculateTierSize is not like expected.')
        
    def testCalculateTileCountUpToTier(self):
        tierSizeInTiles1 = calculateTierSize(self.testCase1['x'],self.testCase1['y'])
        testResponse1 = calculateTileCountUpToTier(tierSizeInTiles1)
        self.logger.debug('Response calculateTileCountUpToTier: %s'%testResponse1)
        self.assertIsNotNone(testResponse1, 'Response for calculateTileCountUpToTier is None.')
        
        tierSizeInTiles2 = calculateTierSize(self.testCase2['x'],self.testCase2['y'])
        testResponse2 = calculateTileCountUpToTier(tierSizeInTiles2)
        self.logger.debug('Response calculateTileCountUpToTier: %s'%testResponse2)
        self.assertIsNotNone(testResponse2, 'Response for calculateTileCountUpToTier is None.')
        
        tierSizeInTiles3 = calculateTierSize(self.testCase3['x'],self.testCase3['y'])
        testResponse3 = calculateTileCountUpToTier(tierSizeInTiles3)
        self.logger.debug('Response calculateTileCountUpToTier: %s'%testResponse3)
        self.assertIsNotNone(testResponse3, 'Response for calculateTileCountUpToTier is None.')

    @unittest.skip('testCreateTiles')
    def testCreateTiles(self):
        tierSizeInTiles1 = calculateTierSize(self.testCase1['x'],self.testCase1['y'])
        tileCountUpToTier1 = calculateTileCountUpToTier(tierSizeInTiles1)
        testResponse1 = createTiles(self.testCase1['path'], tierSizeInTiles1, tileCountUpToTier1, 
                                    self.testCase1['x'],self.testCase1['y'], '/home/mendt/Documents/tmp/tmp', self.logger) 
        self.logger.debug('Response createTiles: %s'%testResponse1)
        self.assertIsNotNone(testResponse1, 'Response for createTiles is None.')
    
    @unittest.skip('testSortTileToTileGroups')  
    def testSortTileToTileGroups(self):
        tierSizeInTiles1 = calculateTierSize(self.testCase1['x'],self.testCase1['y'])
        tileCountUpToTier1 = calculateTileCountUpToTier(tierSizeInTiles1)
        testResponse1 = sortTileToTileGroups(tierSizeInTiles1, tileCountUpToTier1, '/tmp', '/home/mendt/Documents/tmp/tmp')
        self.logger.debug('Response testSortTileToTileGroups: %s'%testResponse1)
        self.assertIsNotNone(testResponse1, 'Response for testSortTileToTileGroups is None.')
    
    @unittest.skip('testSingleFile')
    def testSingleFile(self):
        self.logger.debug('Test file: %s'%self.testCase1['path'])
        tierSizeInTiles1 = calculateTierSize(self.testCase1['x'],self.testCase1['y'])
        testResponse1 = calculateTileCountUpToTier(tierSizeInTiles1)
        self.logger.debug('Response calculateTierSize: %s'%tierSizeInTiles1)
        self.logger.debug('Response calculateTileCountUpToTier: %s'%testResponse1)
     
    #@unittest.skip('testSingleFile1')   
    def testSingleFile1(self):
        path = '/srv/vk/data_archiv/0010000/df_dk_0010001_2352.tif'
        x = 8033
        y = 9281
        self.logger.debug('Test file: %s'%path)
        tierSizeInTiles1 = calculateTierSize(x,y)
        tileCountUpToTier1 = calculateTileCountUpToTier(tierSizeInTiles1)
        testResponse1 = createTiles(path,  tierSizeInTiles1, tileCountUpToTier1, 
                    x,y, '/home/mendt/Documents/tmp/tmp', self.logger) 

      
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()