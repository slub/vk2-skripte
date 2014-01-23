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

