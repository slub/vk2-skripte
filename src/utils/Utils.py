'''
Created on Jan 10, 2014

@author: mendt
'''
import logging

def fileToString(file):
    with open(file, 'r') as myFile:
        data = myFile.read().replace('\n', '')
        return data
    
def createLogger(name, level, logFile=None, formatter=None):
    """ Creates a logger 
    
    Args:
        name (string): name of the logger
        level: log level
        logFile (String): path to logfile 
        formatter: 
    Returns:
        logger
    """
    logging.basicConfig()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logFile and formatter:
        logHandler = logging.FileHandler(logFile)
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        
    return logger
    