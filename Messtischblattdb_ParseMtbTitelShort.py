#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 21, 2013

@author: mendt
'''
import re
import psycopg2.extras
from psycopg2 import IntegrityError
from settings import params_database

class AbstractDB(object):

    def __init__(self, connectionParameter):
        type(self).connectionParameter = connectionParameter
        type(self).connection = psycopg2.connect(type(self).connectionParameter)
    
    def __del__(self):
        self.connection.close()  
           
    def __executeSQLQuery__(self, query=None, values=None, type=None):
        writeSuccess = False
        try:
            cur = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if query != None and (type == None or type == "SELECT"):
                cur.execute(query,(values))
                records = cur.fetchall()
                cur.close()
                return records
            # write support
            if type != None and type == "WRITE":
                cur.execute(query,values)
                cur.close()
                writeSuccess = True
                return True
        except:
            self.connection.rollback()
            raise
        finally:
            if writeSuccess:
                self.connection.commit()
            
    def __toString__(self):
        print(self.connectionParameter)

def checkIfNumber(string):
    try:
        if isinstance(int(string), int):
            return True
    except ValueError:
        return False
    
def parseMesstischblattTitel(titelString):
    print(titelString)
    occurrenceDoublePoints = str(titelString).count(':')    
    if occurrenceDoublePoints == 1:
        ''' Syntax "Meßtischblatt 0495 : Grünheide b. Wilkieten, 1939" '''
        titel_parse_1 = str(titelString).split(":")[1].lstrip() # "Grünheide b. Wilkieten, 1939"
        titel_parse_2 = titel_parse_1.split(",")[0] # "Grünheide b. Wilkieten"
        return titel_parse_2
    if occurrenceDoublePoints == 2:
        ''' Syntax "Messtischblatt : 93 : Rodenäs, 1934 Rodenäs '''
        titel_parse_1 = str(titelString).split(":")[2].lstrip() # "Rodenäs, 1934 Rodenäs"
        titel_parse_2 = titel_parse_1.split(",")[0] # "Rodenäs"
        return titel_parse_2        
    if occurrenceDoublePoints == 0:
        partsAfterSplit = str(titelString).split(' ')
        if checkIfNumber(partsAfterSplit[len(partsAfterSplit) - 1]):
            return partsAfterSplit[len(partsAfterSplit) - 2].rstrip(',')
        else:
            return partsAfterSplit[len(partsAfterSplit) - 1] # "Meßtischblatt Kinten"
    
def getMtbWithTitelAndId(database):
    query = "SELECT id, titel FROM md_core;"
    return database.__executeSQLQuery__(query, [], 'SELECT')

def updateTitelShort(mtbid, titel, database):
    query = "UPDATE md_core SET titel_short = %s WHERE id = %s;"
    values = [titel, mtbid]
    database.__executeSQLQuery__(query, values, 'WRITE')
    return "Set titel \"%s\" for id %s" % (titel, mtbid)

def insertTitelShortIntoMesstischblattDB(database):
    titelRecords = getMtbWithTitelAndId(database)
    for record in titelRecords:
        print "Record titel : %s"%record
        titel = parseMesstischblattTitel(record['titel'])
        print updateTitelShort(record['id'], titel, database)
    
if __name__ == '__main__':
    insertTitelShortIntoMesstischblattDB(AbstractDB("dbname='%s' user='%s' host='%s' password='%s'"%(params_database['db'],
                    params_database['user'],params_database['host'],params_database['password'])))