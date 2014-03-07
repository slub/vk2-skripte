'''
Created on Feb 24, 2014

@author: mendt
'''
import subprocess, math, tempfile, shutil, sys, os, copy, logging, argparse

# set path of the project directory for finding the correct modules
parentPath = os.path.abspath('..')
sys.path.insert(0, parentPath)
sys.path.append(os.path.abspath('.'))

from src.utils.Utils import createLogger

def parseXYSize(imageFile):
    """ This function parse the x,y size of a given image file

    Arguments:
        imageFile {String} Path to a image file
    Return:
        {Dictionary} - value which represents the y size of the file """
    # run gdalinfo command on imageFile and catch the response via Popen
    response = subprocess.Popen("gdalinfo %s"%imageFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    # read the console output line by line
    for line in response.stdout:
        if 'Size is ' in line:
            x,y = line[8:].split(', ')
            #print "X: %s, Y: %s"%(x,y)
            return {'x':float(x),'y':float(y)}
        
def calculateTierSize(imageWidth, imageHeight, tileSize=256):
    """ The function calculate the number of tiles per tier
    
    Arguments:
        imageWidth {Float}
        imageHeight {Float}
        tileSize {Integer} Default is 256 pixel
    Return:
        {Array} """
    tierSizeInTiles = []
    while (imageWidth > tileSize or imageHeight > tileSize):
        tileWidth = imageWidth/tileSize
        tileHeight = imageHeight/tileSize
        tierSizeInTiles.append([math.ceil(tileWidth),math.ceil(tileHeight)])
        tileSize += tileSize
    tierSizeInTiles.append([1.0, 1.0])      
    return tierSizeInTiles
    
def calculateTileCountUpToTier(tierSizeInTiles):
    """ The function caclulate the tileCount up to the top tier
    
    Arguments:
        tileSizeInTiles {Array}
    Return: {Array} """
    tileCountUpToTier = [0]
    tmp_tierSizeInTiles = copy.copy(tierSizeInTiles)
    tmp_tierSizeInTiles.reverse()
    for i in range(1, len(tmp_tierSizeInTiles)):
        value = tmp_tierSizeInTiles[i - 1][0] * tmp_tierSizeInTiles[i - 1][1] + tileCountUpToTier[i - 1]
        tileCountUpToTier.append(value)
    return tileCountUpToTier

def sortTileToTileGroups(tierSizeInTiles, tileCountUpToTier, tileDir, targetPath):
    """ Create the commands for sorting the tile to tile groups 
    
    Arguments:
        tileDir {String}
        tierSizeInTiles {List}
        targetPath {String}
        tileCountUpToTier {List}
    Return: {Dict} """
    template_command_copy = "cp %s %s"
    
    commands = []
    tierSizeInTiles = copy.copy(tierSizeInTiles)
    tierSizeInTiles.reverse()
    tileGroupeDirs = []
    for zoomLevel in range(0, len(tierSizeInTiles)):
        for x in range(0, int(tierSizeInTiles[zoomLevel][0])):
            for y in range(0, int(tierSizeInTiles[zoomLevel][1])):
                tileIndex = x + y * tierSizeInTiles[zoomLevel][0] + tileCountUpToTier[zoomLevel]
                tileGroupIndex = int(math.floor(tileIndex / 256))
                
                # check if the tileGroupIndex is already register. If not do it
                tileGroupeDir = os.path.join(targetPath, 'TileGroup%s'%tileGroupIndex) 
                if not tileGroupeDir in tileGroupeDirs:
                    tileGroupeDirs.append(tileGroupeDir)
                    
                #print "TileGroup: %s, ZoomLevel: %s, X: %s, Y: %s"%(tileGroupIndex,zoomLevel,x,y)   
                   
                source_path = os.path.join(tileDir, '%s-%s-%s.jpg'%(zoomLevel, x, y))
                target_path = os.path.join(tileGroupeDir, '%s-%s-%s.jpg'%(zoomLevel, x, y))
                command = template_command_copy%(source_path, target_path)
                commands.append(command)                

    return {'commands':commands,'tilegroups':tileGroupeDirs}

def createTiles(imgPath, tierSizeInTiles, tileCountUpToTier, imgWidth, imgHeight, targetPath, logger):
    """ The function create via imagemagick a tile pyramid for the given image
    Arguments:
        imgPath {String}
        tierSizeInTiles {List}
        tileCountUpToTier {List}
        imgWidth {Float}
        imgHeight {Float}
        targetPath {String}
        logger {LOGGER}
    Return: {Array} """
    try:
        tmp_dir = tempfile.mkdtemp("", "tmp_", '/home/mendt/Documents/tmp/tmp') # create dir
        
        # sort tiles to group
        # create zoomify directory
        zoomify_dirName = os.path.basename(imgPath).split('.')[0]
        zoomify_dir = os.path.join(targetPath, zoomify_dirName)

        if not os.path.exists(zoomify_dir):
            # calculate different zoom levels for the img
            zoomLevels = []
            i = len(tierSizeInTiles)
            lastImgPath = imgPath
            while i > 0:
                resizePath = os.path.join(tmp_dir, 'zoom-%s.jpg'%i)
                command = '/usr/bin/convert "%s" -strip -resize 50%% -quality 75%% "%s"'%(lastImgPath, resizePath)
                if i == len(tierSizeInTiles):
                    command = '/usr/bin/convert "%s" -strip -quality 75%% "%s"'%(lastImgPath, resizePath)
                logger.debug(command)
                subprocess.check_call(command, shell=True)
                zoomLevels.append(resizePath)
                lastImgPath = resizePath
                i -= 1
             
            # create the tiles
            zoomLevels.reverse()
            i = len(zoomLevels) - 1   
            while i >= 0:
                logger.debug("Zoom %s - %s"%(i, zoomLevels[i]))
                zoom_path = os.path.join(tmp_dir, "%s"%i)
                command = '/usr/bin/convert "%s" -crop 256x256 -set filename:tile "%%[fx:page.x/256]-%%[fx:page.y/256]" +repage +adjoin "%s-%%[filename:tile].jpg"'%(zoomLevels[i], zoom_path)
                logger.debug(command)
                subprocess.check_call(command, shell=True) 
                i -= 1

            os.makedirs(zoomify_dir)
            logger.debug('Target directory: %s'%zoomify_dir)
            
            
            sortTiled = sortTileToTileGroups(tierSizeInTiles, tileCountUpToTier, tmp_dir, zoomify_dir)
            # create tilegroup directorys
            for tileGroup in sortTiled['tilegroups']:
                if not os.path.exists(tileGroup):
                    os.makedirs(tileGroup)
                    
            # copy tiles in correct tilegroup directory
            for command in sortTiled['commands']:
                subprocess.check_call(command, shell=True)
        
            # write properties file 
            xml_string = "<IMAGE_PROPERTIES WIDTH=\"%s\" HEIGHT=\"%s\" NUMTILES=\"%s\" NUMIMAGES=\"1\" VERSION=\"1.8\" TILESIZE=\"%s\" />"%(
                                int(imgWidth), int(imgHeight), len(sortTiled['commands']), 256)
            logger.debug('Zoomify Properties: %s'%xml_string)
            imagePropertiesFile = open(os.path.join(zoomify_dir, 'ImageProperties.xml'), 'w')
            imagePropertiesFile.write(xml_string)
            imagePropertiesFile.close()
        return zoomify_dir       
        
    except:
        print >> sys.stderr,"Unexpected error:", sys.exc_info()[0]
        raise Exception("Error while running subprocess via commandline!")
    finally:
             try:
                 # delete tmp_dir
                 shutil.rmtree(tmp_dir) 
             except OSError, e:
                 # code 2 - no such file or directory
                 if e.errno != 2:
                     raise

if __name__ == '__main__':
    # example command: ../python_env/bin/python CreateZoomifyTiles.py --input_file /home/mendt/mtb_paths_exist.md --tif_dir /srv/vk/data_archiv/0010000
    # argument parser for giving parameters to the script
    parser = argparse.ArgumentParser(description = 'This scripts calculates zoomify tiles".', prog = 'Script CreateZoomifyTiles.py')
    parser.add_argument('--input_file', help='text file which contains a list on input arguments. If missing the script try\'s to run in test modus')
    parser.add_argument('--tif_dir', help='Directory where the tiff\'s are placed.')
    parser.add_argument('--target_dir', default='/home/mendt/Documents/tmp/tmp', help='Directory where to safe new zoomify tiles')
    args = parser.parse_args()
    
    logger = createLogger('Zoomify', logging.DEBUG)
    
    if args.input_file and args.tif_dir:
        logger.info('Try to parse image paths from %s'%args.input_file)
        inputImages = []
        f = open(args.input_file)
        for line in f:
            line_strip = line.rstrip('\n')
            image_path = os.path.join(args.tif_dir, line_strip[line_strip.rfind('/')+1:])
            inputImages.append(image_path)
    else:
        logger.info('Script run\'s in test mode.')
        inputImages = [
            '/home/mendt/Documents/tmp/df_dk_0010001_0294.tif',
            '/home/mendt/Documents/tmp/df_dk_0010001_0293.tif',
            '/home/mendt/Documents/tmp/df_dk_0010001_0292.tif',
            '/home/mendt/Documents/tmp/df_dk_0010001_0194.tif',
            '/home/mendt/Documents/tmp/df_dk_0010001_0193.tif',
            '/home/mendt/Documents/tmp/df_dk_0010001_0192.tif'
        ]
    
    logger.info('Start calculation of zoomify tiles.')
    for image in inputImages:
        logger.info('Calculating zoomify tiles for %s'%image)
        size = parseXYSize(image)
        tierSizeInTiles = calculateTierSize(size['x'],size['y'])
        tileCountUpToTier = calculateTileCountUpToTier(tierSizeInTiles)
        response = createTiles(image, tierSizeInTiles, tileCountUpToTier, size['x'], size['y'], args.target_dir, logger)
        logger.info('Finished calculating zoomify tiles for %s'%image) 