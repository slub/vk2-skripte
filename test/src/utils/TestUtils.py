'''
Created on Feb 20, 2014

@author: mendt
'''
import unittest
from settings import sqlalchemy_engine
from src.models.Meta import initializeDb
from src.utils.Utils import degrees2Tile, calculateTileBounds, createRenderListCommand, getMesstischblaetterOriginalPaths

class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dbsession = initializeDb(sqlalchemy_engine)

    def testDegrees2Tile(self):
        xMin = 5.75067248805447
        yMin = 47.097640863915906
        xMax = 23.9110728804318
        yMax = 57.28030106430717
        response = degrees2Tile(yMin, xMin, 13)
        response1 = degrees2Tile(yMax, xMax, 13)
        self.assertEqual(response, (4226, 2878), 'Function: testDegrees2Tile - Response is not like expected')
        self.assertEqual(response1, (4640, 2497), 'Function: testDegrees2Tile - Response is not like expected')

    def testCalculateTileBounds(self):
        bounds = [5.75067248805447, 47.097640863915906, 23.9110728804318, 57.28030106430717]
        minZoom = 7
        maxZoom = 17
        response = calculateTileBounds(bounds, minZoom, maxZoom)
        self.assertIsNotNone(response, 'Function: testCalculateTileBounds - Response is none')
        self.assertTrue(isinstance(response, list), 'Function: testCalculateTileBounds - Response is not a list.')
        
        for record in response:
            print "Zoom: %(zoom)s - MinX: %(minx)s, MinY: %(miny)s, MaxX: %(maxx)s, MaxY: %(maxy)s."%record
            
    def testCreateRenderListCommand(self):
        bounds = [5.75067248805447, 47.097640863915906, 23.9110728804318, 57.28030106430717]
        minZoom = 7
        maxZoom = 17
        response = createRenderListCommand(bounds, minZoom, maxZoom, '/srv/vk/data_archiv/mod_tile', 10)
        self.assertIsNotNone(response, 'Function: testCreateRenderListCommand - Response is none')
        self.assertTrue(isinstance(response, str), 'Function: testCreateRenderListCommand - Response is not a str.')
        print response

    @unittest.skip('Skip Loading tile config default at /osm_tiles/ for')
    def testGetMesstischblaetterOriginalPaths(self):
        response = getMesstischblaetterOriginalPaths(self.dbsession, '/home/mendt/mtb_paths.md')
        self.assertIsNotNone(response, 'Function: testGetMesstischblaetterOriginalPaths - Response is none')
        self.assertTrue(isinstance(response, str), 'Function: testGetMesstischblaetterOriginalPaths - Response is not a str.')
        print response
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()