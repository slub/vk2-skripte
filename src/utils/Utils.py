'''
Created on Jan 10, 2014

@author: mendt
'''

def fileToString(file):
    with open(file, 'r') as myFile:
        data = myFile.read().replace('\n', '')
        return data