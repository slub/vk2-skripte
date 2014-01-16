'''
Created on Jan 9, 2014

@author: mendt
'''
import unittest
from sqlalchemy.orm.session import Session
from settings import sqlalchemy_engine
from src.models.Meta import initializeDb

class TestMeta(unittest.TestCase):
    
    def testInitializeDb(self):
        dbSession = initializeDb(sqlalchemy_engine)
        self.assertTrue(isinstance(dbSession, Session), "Could not correctly initialize the sql alchemy session object.")