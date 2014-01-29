vk2-skripte
===========

Dieses Repository enthält verschiedene Skripte für Aufgaben des Virtuellen Kartenforums 2.0

Install
=======

	1.) Install virtual environment
		- virtualenv path/to/env
   	2.) Add side packages to the virtual environment
        	- ln -s /usr/lib/python2.7/dist-packages/gdal* ~/path/to/env/lib/python2.7/site-packages/
		- ln -s /usr/lib/python2.7/dist-packages/MapScript-6.0.1.egg-info ~/path/to/env/lib/python2.7/site-packages/
		- ln -s /usr/lib/python2.7/dist-packages/GDAL-1.9.0.egg-info ~/path/to/env/lib/python2.7/site-packages/
		- ln -s /usr/lib/python2.7/dist-packages/mapscript.py* ~/path/to/env/lib/python2.7/site-packages/
		- ln -s /usr/lib/python2.7/dist-packages/_mapscript.so ~/path/to/env/lib/python2.7/site-packages/
	3.) Install python librarys for the virtualenv
		- ~/path/to/env/bin/easy_install SQLAlchemy psycopg2 WebHelpers requests

Run Tests
=========

	1.) Running the tests

		- ~/path/to/env/bin/python test/TestSuite.py

Georeferencer script
====================
This scripts compute a persitent georeference result. It reads the oben georeference processes from the database 
and computes a georeference result for them. After that it updates the database state and push a metadata record
for the georeference messtischblatt to a csw geonetwork instance.

The script could be run in testing or in production mode. In case of production mode the update database will run
with a commit flag.

	../python_env/bin/python Georeferencer.py -modus=production

For correct running in a cronjob environment set in the head of the Georeferencer.py script the following path variable

	sys.path.append('~/path/to/project/vk2-skripte')


UpdateMappingService script 
===========================
This scripts is controllable via command line. It's update the virtual datasets for the giving timestamps and persist the 
change in the database. It also could update cache, if wanted. For further help see

../python_env/bin/python UpdateMappingService.py -h

Example command:

../python_env/bin/python UpdateMappingService.py --mode 'slim' --host ... --password '...' --user '...' --db '..' --tmp_dir '.../tmp' '.../tmp'


