#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: выкачивание с openaerialmap
# Author: Artem Svetlov <artem.svetlov@nextgis.com>
# Copyright: 2018, NextGIS <info@nextgis.com>


import os
import requests
import urllib2
import json



class Processor:

    def __init__(self):
        pass

    def oam_download(self):
        
        endpoint = 'https://api.openaerialmap.org/meta'
        query = endpoint + '?bbox=37.3193,55.4899,37.9457,56.0097&gsd_to=1&gsd_from=0.001&acquisition_from=2014-01-01&acquisition_to=2018-01-01&limit=100'
        print query
        os.system('wget -O response.json "'+query + '"')
        listresp = json.load((open('response.json')))
        urllist = open('urllist.txt', 'w')
        for scene in listresp['results']:
            urllist.write(scene['uuid']+"\n")
            print scene['uuid']
        urllist.close()

        #paralel download of all files from file list 
        os.system('cat urllist.txt | parallel --gnu "wget --timestamping {}"')

        #call other script
        #merge all rasters in folder
        print 'time python ../raster_super_merge/run.py'
        #os.system('time python ../raster_super_merge/run.py ')



import argparse
def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='''Download Moscow imagery from OpenAerialMap and merge to one file
    ''',
            formatter_class=PrettyFormatter)



    parser.epilog = \
        '''Samples: 
%(prog)s 
''' \
        % {'prog': parser.prog}
    return parser


parser = argparser_prepare()
args = parser.parse_args()
processor=Processor()
processor.oam_download()


