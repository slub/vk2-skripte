'''
Created on Jan 23, 2014

@author: mendt

Before running the Tests please check:
    - The settings.py is valide
    - A tomcat is running on localhost:8080
    - The database / file system is valide (for processing messtischlbatt results)
    
'''
import unittest, sys, os
# set path of the project directory for finding the correct modules
parentPath = os.path.abspath('.')
sys.path.insert(0, parentPath)



from test.src.models.TestMeta import TestMeta
from test.scripts.TestGeoreferencer import TestGeoreferencer
from test.src.csw.TestChildMetadataBinding import TestChildMetadataBinding
from test.src.csw.TestCswTransactionBinding import TestCswTransactionBinding
from test.src.csw.TestInsertMetadata import TestInsertMetadata
from test.src.csw.TestServiceMetadataBinding import TestServiceMetadataBinding


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMeta))
    suite.addTests(loader.loadTestsFromTestCase(TestChildMetadataBinding))
    suite.addTests(loader.loadTestsFromTestCase(TestCswTransactionBinding))
    suite.addTests(loader.loadTestsFromTestCase(TestInsertMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceMetadataBinding))
    suite.addTests(loader.loadTestsFromTestCase(TestGeoreferencer))
    
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(test_suite())