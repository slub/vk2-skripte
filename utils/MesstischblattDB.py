# -*- coding: utf-8 -*- 
from utils.Geometry import createBBoxFromPostGISString
from utils.GdalInfoBinding import GdalInfoConnector

def createMesstischblattObj(dictRow):
    # create the wrapper object for the db response for messtischblatt
    mtbObj = WrapperDictionaryObj(dictRow)
    # add bbox object to the wrapper object
    setattr(mtbObj,'bbox',createBBoxFromPostGISString(mtbObj.st_astext,4314))
    return mtbObj

class WrapperDictionaryObj(object):
    '''The recursive class for building and representing objects with.'''
    def __init__(self, data):
        for key, value in data.iteritems():
            setattr(self, key, self._wrap(value))
            
    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return WrapperDictionaryObj(value) if isinstance(value, dict) else value

'''
Functions for getting the gcps.
'''   
def getGCPsAsString(unorderedPixels, verzeichnispfad, georefCoords):
    pure_gcps = getGCPs(unorderedPixels, verzeichnispfad, georefCoords)
    str_gcps = []
    for tuple in pure_gcps:
        string = " ".join(str(i) for i in tuple[0])+", "+" ".join(str(i) for i in tuple[1])
        str_gcps.append(string)
    return str_gcps

def getGCPs(unorderedPixels, verzeichnispfad, georefCoords):
        # transformed the pixel coordinates to the georef coordinates by recalculating the y values, 
        # because of a different coordinate origin
        transformedUnorderedPixels = []
        gdalConnector = GdalInfoConnector(verzeichnispfad)
        ySize = gdalConnector.datafile.RasterYSize
        for tuple in unorderedPixels:
            transformedUnorderedPixels.append((tuple[0],ySize-tuple[1]))

        # now order the pixel coords so that there sorting represents the order llc, ulc, urc, lrc
        transformedOrderedPixels = orderPixels(transformedUnorderedPixels)

        # now create the gcp list
        try:
            gcpPoints = []
            for i in range(0,len(transformedOrderedPixels)):
                pixelPoints = (transformedOrderedPixels[i][0],transformedOrderedPixels[i][1])
                georefPoints = (georefCoords[i][0],georefCoords[i][1])
                gcpPoints.append((pixelPoints,georefPoints))
            return gcpPoints
        except:
            raise  
               
def orderPixels(unorderdPixels):
    """
    Function brings a list of tuples which are representing the clipping parameter from the client 
    in the order llc ulc urc lrc and gives them back at a list. Only valide for pixel coords
        
    @param clippingParameterList: list whichcomprises 4 tuples of x,y coordinates
    """
    xList = []
    yList = []
    for tuple in unorderdPixels:
        xList.append(tuple[0])
        yList.append(tuple[1])
             
    orderedList = [0, 0, 0, 0] 
    xList.sort() 
    yList.sort()
    for tuple in unorderdPixels:
        if (tuple[0] == xList[0] or tuple[0] == xList[1]) and \
            (tuple[1] == yList[2] or tuple[1] == yList[3]):
            orderedList[0] = tuple
        elif (tuple[0] == xList[0] or tuple[0] == xList[1]) and \
            (tuple[1] == yList[0] or tuple[1] == yList[1]):
            orderedList[1] = tuple 
        elif (tuple[0] == xList[2] or tuple[0] == xList[3]) and \
            (tuple[1] == yList[0] or tuple[1] == yList[1]):
            orderedList[2] = tuple 
        elif (tuple[0] == xList[2] or tuple[0] == xList[3]) and \
            (tuple[1] == yList[2] or tuple[1] == yList[3]):
            orderedList[3] = tuple 
    return orderedList 

    

