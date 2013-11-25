#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 21, 2013

@author: mendt
'''
import unittest
from Messtischblattdb_ParseMtbTitelShort import parseMesstischblattTitel

class Test(unittest.TestCase):

    def testParseMesstischblattTitel(self):
        self.assertEqual(parseMesstischblattTitel('Messtischblatt 0192 : Nimmersatt, 1939 Nimmersatt'), 'Nimmersatt')
        self.assertEqual(parseMesstischblattTitel('Messtischblatt 0193 : Dtsch. Crottingen, 1940 Dtsch. Crottingen'), 'Dtsch. Crottingen')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 0495 : Grünheide b. Wilkieten, 1939'), 'Grünheide b. Wilkieten')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt Kinten'), 'Kinten')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 32, neue Nr. 0697 : Ackmonischken, 1939'), 'Ackmonischken')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 0791, 0792 : Pillkoppen, 1939'), 'Pillkoppen')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 78 : Norburg (Insel Alsen), 1879'), 'Norburg (Insel Alsen)')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 1973/1974 (Doppelblatt) : Werder/Potsdam-Süd, 1912'), 'Werder/Potsdam-Süd')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 92.(3003) : Rückersdorf (Sächs.) - Ronneburg (Preuß.), 1920'), 'Rückersdorf (Sächs.) - Ronneburg (Preuß.)')
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 5333 : Bad Blankenburg / Schwarzatal, 1938'), 'Bad Blankenburg / Schwarzatal')    
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 1876 :Gr. Paglau, 1940'), 'Gr. Paglau')
        self.assertEqual(parseMesstischblattTitel('Messtischblatt : 93 : Rodenäs, 1934 Rodenäs'), 'Rodenäs')  
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt 2325 Niendorf'), 'Niendorf')  
        self.assertEqual(parseMesstischblattTitel('Meßtischblatt Radeberg, 1910'), 'Radeberg')              

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()