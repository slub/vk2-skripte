'''
Created on Jan 10, 2014

@author: mendt
'''
import logging, math, os.path
from settings import sqlalchemy_engine
from src.models.Meta import initializeDb
from src.models.Messtischblatt import Messtischblatt

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

def degrees2Tile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def calculateTileBounds(bounds, minZoom, maxZoom):
    list = []
    for x in range(minZoom, maxZoom+1):
        minTileCoords = degrees2Tile(bounds[1], bounds[0], x)
        maxTileCoords = degrees2Tile(bounds[3], bounds[2], x)
        list.append({'minx':minTileCoords[0],'maxy':minTileCoords[1],'maxx':maxTileCoords[0],'miny':maxTileCoords[1],'zoom':x})
    return list

def createRenderListCommand(bounds, minZoom, maxZoom, tileDir, threads):
    tilePyramid = calculateTileBounds(bounds, minZoom, maxZoom)
    response_command = ""
    for record in tilePyramid:
        record['tiledir'] = tileDir
        record['threads'] = threads
        response_command += "render_list --all --min-x=%(minx)s --min-y=%(miny)s --max-x=%(maxx)s --max-y=%(maxy)s --tile-dir \'%(tiledir)s\' --min-zoom=%(zoom)s --max-zoom=%(zoom)s -n %(threads)s && "%record
    return response_command
    
def getMesstischblaetterOriginalPaths(dbsession, path):
    allMtbs = Messtischblatt.all(dbsession)
    file = open(path, 'wb')
    for mtb in allMtbs:
        if mtb.archivpfad_tif_original is not None:
            archiv_pfad = mtb.archivpfad_tif_original[str(mtb.archivpfad_tif_original).find('master'):]
            file.write("/san/archiv/digitalisate/bilder/%s\n"%archiv_pfad) 
    file.close()
    return path

def checkMesstischblatterOriginalPaths(dbsession, path):
    allMtbs = Messtischblatt.all(dbsession)
    nr = 0
    file = open(path, 'wb')
    for mtb in allMtbs:
        if mtb.archivpfad_tif_original is not None:
            archiv_pfad = "/srv/vk/data_archiv/0010000/%s"%mtb.archivpfad_tif_original[str(mtb.archivpfad_tif_original).find('df_dk_'):]
            if (os.path.isfile(archiv_pfad)):
                file.write("%s\n"%archiv_pfad) 
                nr += 1
                print "Nr. %s: %s"%(nr, archiv_pfad) 
    return path

def getMesstischblaetterOriginalPathsRest(dbsession, path):
    allMtbs = Messtischblatt.all(dbsession)
    file = open(path, 'wb')
    for mtb in allMtbs:
        if mtb.archivpfad_tif_original is not None:
            exist_path = "/srv/vk/data_archiv/0010000/%s"%mtb.archivpfad_tif_original[str(mtb.archivpfad_tif_original).find('df_dk_'):]
            if not (os.path.isfile(exist_path)):
                 archiv_pfad = mtb.archivpfad_tif_original[str(mtb.archivpfad_tif_original).find('master'):]
                 file.write("/san/archiv/digitalisate/bilder/%s\n"%archiv_pfad) 
    file.close()
    return path
                
        
if __name__ == "__main__":
    dbsession = initializeDb(sqlalchemy_engine)
    checkMesstischblatterOriginalPaths(dbsession, '/home/mendt/Documents/tmp/tmp/mtb_paths.md')
    #getMesstischblaetterOriginalPathsRest(dbsession, '/home/mendt/mtb_paths_rest.md')
    