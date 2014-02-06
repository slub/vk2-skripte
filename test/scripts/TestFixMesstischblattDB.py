'''
Created on Jan 28, 2014

@author: mendt
'''
import unittest, logging, sys, os

# set path of the project directory for finding the correct modules
parentPath = os.path.abspath('../..')
sys.path.insert(0, parentPath)
sys.path.append(os.path.abspath('.'))

from settings import sqlalchemy_engine
from src.models.Meta import initializeDb
from src.models.Messtischblatt import Messtischblatt
from src.models.MetadatenBildmedium import MetadatenBildmedium
from src.utils.Utils import createLogger
from scripts.FixMesstischblattDB import getBrokenZoomifyProps, stripZoomifyProps

class TestFixMesstischblattDB(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.logger = createLogger('sqlalchemy.engine', logging.DEBUG)
        cls.dbsession = initializeDb(sqlalchemy_engine)
        
    def test_getBrokenZoomifyProps(self):
        response = getBrokenZoomifyProps(self.dbsession)
        print "Response test_getBrokenZoomifyProps - %s"%response
        self.assertTrue(isinstance(response, list), 'Function test_getBrokenZoomifyProps - Failed because it\'s not a list')
        if len(response) > 0:
            self.assertTrue(isinstance(response[0], MetadatenBildmedium), 'Function test_getBrokenZoomifyProps - Failed because it\'s list doesn\'t contain orm for MetadatenBildmedium.')
        
    def test_stripZoomifyProps(self):
        response = stripZoomifyProps('http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5060_1930/ImageProperties.xmlhttp://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5060_1933/ImageProperties.xml')
        print "Response test_stripZoomifyProps - %s"%response
        self.assertTrue(isinstance(response, str), 'Function test_stripZoomifyProps - Failed because it\'s not a string')
        self.assertEqual(response, 'http://fotothek.slub-dresden.de/zooms/df/dk/0010000/df_dk_0010001_5060_1930/ImageProperties.xml', 
                         'Function test_stripZoomifyProps - Response is not like expected.')
            
     
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestGeoreferencer.testName']
    unittest.main()