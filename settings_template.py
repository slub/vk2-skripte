'''
Created on Nov 18, 2013

@author: mendt
'''
params_database = {
    'host':'x.x.x.x',
    'user':'username',
    'password':'password',
    'db':'database',    
}

params_gdal = {
    'tmp_dir': '../tmp/tmp',
    'target_dir': '../tmp/tmp/taget',
    'overviewLevels': '64 128 256 512'
}

params_mtbs = {
    'layerid': 87
}

params_mapcache = {
    'threads': 2
}

sqlalchemy_engine = 'postgresql+psycopg2://user:password@host:5432/database' # has to be change


'''
Parameter for automatic creation of the metadata records which are conform to iso19115
'''
templates = {
    'child': '~/vk2-skripte/metadaten-templates/template.mtb.child.xml',
    'service': '~/vk2-skripte/metadaten-templates/template.mtb.service.xml',
    'insert': '~/vk2-skripte/metadaten-templates/template.request.insert.xml',
    'tmp_dir': '~/tmp'
}

gn_settings = {
    'gn_baseURL': 'geonetwork_host', # has to be change
    'gn_loginURI':'/geonetwork/j_spring_security_check',
    'gn_logoutURI':'/geonetwork/j_spring_security_logout',
    'gn_cswTransactionURI':'/geonetwork/srv/eng/csw-publication',
    'gn_username':'username', # has to be change
    'gn_password':'password'     # has to be change
}

srid_database = 4314