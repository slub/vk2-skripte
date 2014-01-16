'''
Created on May 30, 2013

@author: mendt
'''
import unittest
from osgeo import gdal, osr

import gdalinfo
from Geometry import *

def GDALInfoParseCorner(dataset,x,y,epsg):
    '''
    GDALInfoParseCorner based of code from gdalinfo.py out of the sample folder from the gdal/python
    bindings
    '''
    #Transform the point into georeferenced coordinates.
    adfGeoTransform = dataset.GetGeoTransform(can_return_null = True)
    if adfGeoTransform is not None:
        dfGeoX = adfGeoTransform[0] + adfGeoTransform[1] * x \
            + adfGeoTransform[2] * y
        dfGeoY = adfGeoTransform[3] + adfGeoTransform[4] * x \
            + adfGeoTransform[5] * y

    else:
        print("(%7.1f,%7.1f)" % (x, y ))
        return False

    # create points and returns it
    if abs(dfGeoX) < 181 and abs(dfGeoY) < 91:
        return Point(dfGeoX,dfGeoY,epsg)
    else:
        raise

class GdalInfoConnector(object):
    '''
    GdalInfoConnector based of code from gdalinfo.py out of the sample folder from the gdal/python
    bindings
    '''

    def __init__(self,pathToRasterFile):
        self.path = pathToRasterFile
        self.datafile = gdal.Open(pathToRasterFile,gdal.GA_ReadOnly)
        if self.datafile is None:
            print("gdalinfo failed - unable to open '%s'." % str(pathToRasterFile) )
            raise
    
    def __str__(self):
        gdalinfo.main(['foo',self.path])
        return True
    
    def extractImageStructure(self):
        '''
        @param Dictionary: IMAGE_STRUCTURE
        '''
        imageStructureMD = self.datafile.GetMetadata_List("IMAGE_STRUCTURE")
        dictImageStructureMD = {}
        if imageStructureMD is not None and len(imageStructureMD) > 0:
            for metadata in imageStructureMD:
                tmp = str(metadata).split("=")
                dictImageStructureMD[tmp[0]]=tmp[1]
        return dictImageStructureMD

    def extractBandInformation(self):
        '''
        assumption that the structure for all bands are the same
        
        @param Dictionary: {"Block":"value","Overviews":"value"}
        '''
        dictBandInformation = {}
        if range(self.datafile.RasterCount) > 0:
            band = self.datafile.GetRasterBand(1)
            # extract block size out of the band 
            (nBlockXSize, nBlockYSize) = band.GetBlockSize()
            overviewcount = band.GetOverviewCount()
            dictBandInformation["Block"]="%dx%d"%(nBlockXSize, nBlockYSize)
            dictBandInformation["Overviews"]="%d"% overviewcount
        return dictBandInformation

    def extractBoundingBoxInformation(self):
        '''
        @param BoundingBox: Representing the BoundingBox of the Rasterfile. 
        '''
        
        def extractEPSGCode(projection):
            if projection is not None:
                crsBinding = osr.SpatialReference()
                if crsBinding.ImportFromWkt(projection) == gdal.CE_None:
                    return crsBinding.GetAttrValue("AUTHORITY",1) 
                        
        projection = self.datafile.GetProjectionRef()
        epsg = extractEPSGCode(projection)
        llc = GDALInfoParseCorner(self.datafile,0.0,self.datafile.RasterYSize,epsg)
        ulc = GDALInfoParseCorner(self.datafile,0.0,0.0,epsg)
        urc = GDALInfoParseCorner(self.datafile,self.datafile.RasterXSize, 0.0,epsg)
        lrc = GDALInfoParseCorner(self.datafile,self.datafile.RasterXSize,self.datafile.RasterYSize,epsg)
        bbox = BoundingBox(llc.x,llc.y,urc.x,urc.y,epsg)
        return bbox

    def extractPureExtentInformation(self):
        pureExtent = [0,0,self.datafile.RasterXSize,self.datafile.RasterYSize]
        return pureExtent
        
    