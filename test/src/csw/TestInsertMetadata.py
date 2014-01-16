'''
Created on Jan 9, 2014

@author: mendt
'''    
import unittest
import logging
import tempfile
import shutil
import os
from settings import sqlalchemy_engine, templates, gn_settings
from src.models.Meta import initializeDb
from src.csw.InsertMetadata import insertMetadata, createTemporaryCopy, getMetadataForMesstischblatt, updateMetadata
from src.csw.CswTransactionBinding import gn_transaction_delete
class TestInsertMetadata(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger('sqlalchemy.engine')
        cls.dbSession = initializeDb(sqlalchemy_engine)
        
    def testInsertMetadata(self):
        gn_transaction_delete('df_dk_0010001_0192', gn_settings['gn_username'], gn_settings['gn_password'], self.logger)
        response = insertMetadata(id=71051490,db=self.dbSession,logger=self.logger)
        self.assertIsNotNone(response, "InsertMetadata should pass, but fails.")
        gn_transaction_delete('df_dk_0010001_0192', gn_settings['gn_username'], gn_settings['gn_password'], self.logger)
        
    def testInsertMetadata_1(self):
        gn_transaction_delete('df_dk_0010001_1116', gn_settings['gn_username'], gn_settings['gn_password'], self.logger)
        response = insertMetadata(id=71051613,db=self.dbSession,logger=self.logger)
        self.assertIsNotNone(response, "InsertMetadata should pass, but fails.")
        gn_transaction_delete('df_dk_0010001_1116', gn_settings['gn_username'], gn_settings['gn_password'], self.logger)
       
    def testCreateTemporaryCopy(self):
        try:
            tmpDirectory = tempfile.mkdtemp('', 'tmp_', templates['tmp_dir'])
            mdFile = createTemporaryCopy(templates['child'], tmpDirectory, 'xml')
            self.assertTrue(isinstance(mdFile,str), 'Function: testCreateTemporaryCopy - failed because response is not a string.')
            self.assertTrue(os.path.isfile(mdFile), 'Function: testCreateTemporaryCopy - failed because response is not a existing file')
        except:
            raise
        finally:
            shutil.rmtree(tmpDirectory)
        
    def testGetMetadataForMesstischblatt(self):
        response = getMetadataForMesstischblatt(id=71051490,db=self.dbSession,logger=self.logger)
        self.assertIsNotNone(response, 'Function: testGetMetadataFormesstischblatt - failed because response is none.')
     
            