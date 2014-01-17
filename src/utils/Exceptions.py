'''
Created on Jan 17, 2014

@author: mendt
'''

class GeoreferenceProcessNotFoundError(Exception):
    """ Exception raised if there is not georeference process waiting for process 
        
        Attributes:
            msg  -- explanation of the error
    """
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
        
class GeoreferenceProcessingError(Exception):
    """ Exception raised if there are problems while trying to compute a georeference process result 
        
        Attributes:
            msg  -- explanation of the error
    """
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)        