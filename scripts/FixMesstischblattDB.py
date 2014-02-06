#!/usr/bin/env python
# -*- coding: utf-8 -*-
#/******************************************************************************
# * $Id: UpdateMappingService.py 2014-01-28 jmendt $
# *
# * @deprecated: delete > new script is UpdateMappingService
# * Project:  Virtuelles Kartenforum 2.0
# * Purpose:  Fix different errors in the messtischblatt db
# * Author:   Jacob Mendt
# * @todo:    Fix errors in the messtischblatt db
# *
# *
# ******************************************************************************
# * Copyright (c) 2014, Jacob Mendt
# *
# * Permission is hereby granted, free of charge, to any person obtaining a
# * copy of this software and associated documentation files (the "Software"),
# * to deal in the Software without restriction, including without limitation
# * the rights to use, copy, modify, merge, publish, distribute, sublicense,
# * and/or sell copies of the Software, and to permit persons to whom the
# * Software is furnished to do so, subject to the following conditions:
# *
# * The above copyright notice and this permission notice shall be included
# * in all copies or substantial portions of the Software.
# *
# * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# * DEALINGS IN THE SOFTWARE.
# ****************************************************************************/'''
import logging
from sqlalchemy.orm.session import Session

from settings import sqlalchemy_engine
from src.models.Meta import initializeDb
from src.utils.Utils import createLogger
from src.models.Messtischblatt import Messtischblatt
from src.models.MetadatenBildmedium import MetadatenBildmedium

def getBrokenZoomifyProps(session):
    """ Get bildmedium object with broken zoomify properties     
        Args:
            session 
            logger
        Returns:
            list [Messtischblatt]
    """
    bildmedien = MetadatenBildmedium.all(session)
    response = []
    for bildmedium in bildmedien:
        if bildmedium.zoomify.count('http://') > 1:
            response.append(bildmedium)
    return response
            
def stripZoomifyProps(zoomify_props):
    """ get broken zoomify props and parse a correct out of it
        Args:
            zoomify_props (string)
        Returns:
            string
    """
    correctEndIndex = zoomify_props.index('.xml') + 4
    return zoomify_props[:correctEndIndex]

def fixBrokenZoomifyProps(session, logger):
    logger.info('Start fixing broken zoomify properties ...')

    brokenZoomifyMedien = getBrokenZoomifyProps(session)    
    for medium in brokenZoomifyMedien:
        logger.info('Fixing zoomify props for medium with id %s.'%medium.id)
        correct_zoomify = stripZoomifyProps(medium.zoomify)
        
        # fix in md_bildmedium
        medium.zoomify = correct_zoomify
        
        # fix in messtischblatt
        mtb = Messtischblatt.by_id(medium.id, session)
        mtb.zoomify_properties = correct_zoomify
        
    logger.info('Finish fixing broken zoomify properties.')

if __name__ == '__main__':
    session = initializeDb(sqlalchemy_engine)
    logger = createLogger('sqlalchemy.engine', logging.DEBUG)
    fixBrokenZoomifyProps(session, logger)
    session.commit()