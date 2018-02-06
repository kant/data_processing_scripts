﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: 
# Author: Artem Svetlov <artem.svetlov@nextgis.com>
# Copyright: 2016-2018, NextGIS <info@nextgis.com>


#import progressbar



def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)


import os 
import shutil
files = list()

dirpath = os.getcwd()

compress = '-co COMPRESS=JPEG -co JPEG_QUALITY=50'
# generate filelist from dir
import os
for file in os.listdir(dirpath):
    if (file.endswith(".tif")) or (file.endswith(".tiff")):
        #print(file)
        files.append(file)

# output dir is same as input
stack_dir = os.path.join(dirpath,'stack')
if not os.path.exists(stack_dir):
    os.makedir(stack_dir)

i=0
# for each raster
for file in files:
    i=i+1
    if i == 1:
        #копирование первого растра
        #на всякий случай без shutil чтоб заработало на винде
        file_result = os.path.join(stack_dir,str(i))+'.tiff'
        file_current = file
        cmd = 'gdal_translate  -o {file_result} {file_current}'.format(file_result=file_result,file_current=file_current)
        print cmd
        os.system(cmd)
    #print file
    if i > 2:
        file_result = os.path.join(stack_dir,str(i))+'.tiff'
        file_prev = os.path.join(stack_dir,str(i-1))+'.tiff'
        file_current = file
        cmd = 'gdal_merge -of GTiff -o {file_result} {file_prev} {file_current}'.format(file_result = file_result,file_prev=file_prev,file_current=file_current)
        print cmd
        os.system(cmd)
# merge prev raster with next and save to stack dir
