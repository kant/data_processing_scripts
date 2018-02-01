﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Project: 
# Author: Artem Svetlov <artem.svetlov@nextgis.com>
# Copyright: 2016-2018, NextGIS <info@nextgis.com>


'''

'''

#импорт модулей


print 'signal'


import config
import os
import psycopg2
import psycopg2.extras
import subprocess
import progressbar

def import_file2postgis(filename,tablename,conn_string):
    cmd='''ogr2ogr -progress -overwrite -f "PostgreSQL" PG:"{conn_string}" {filename}  -nln {tablename}'''.format(filename=filename,conn_string=conn_string,tablename=tablename)
    print cmd
    os.system(cmd)

def ogrlineref_parse_result(text):
    '''На вход поступает строка, которую выдаёт утилита ogrlineref
        The position for distance 7665.410000 is lat:7320584.949110, long:591444.684970, height:0.000000
        Возвращает lat,lon
    '''
    #операции со строками
    
    pos = text.find('lat:')
    begin = text.find('lat:') + len('lat:') #позиция начала цифр после lat:
    end = text.find(',',begin) #позиция первой запятой после lat
    lat = text[begin:end] #получение части строки по номерам букв

    pos = text.find('long:')
    begin = text.find('long:') + len('long:') 
    end = text.find(',',begin) 
    lon = text[begin:end] 

    return lat,lon


#файл с реперами
src_repers_datasource_name = '../../../data/serv_UTM.shp'
#имя атрибута с пикетом в слое реперов
pos_field_name = 'Serv'
#промежуточный файл с сегментами
rsrc_parts_datasource_name = '../../../data/paths.shp'
#файл с точками заданными пикетами. Сейчас требуется чтоб это был слой с геометрией
measurements_layer_path = '../../../data/VTD2016_1.shp'
#название поля в measurements_layer_path
measurements_dist_field = 'dist_odom'
#файл с трассой. Реализовано для слоя с одной линией
src_line_datasource_name = '../../../data/Pipe_Line_UTM.shp'
#путь куда запишется слой, в котором точки будут перетянуты на линию
#points_on_lines_name = '../../../data/measurements_geo.shp'

#код epsg, в которой все слои
srid = 32643



#подключение к БД

#Define our connection string
conn_string = config.postgresql_connection_string

 
# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect(conn_string)

conn.autocommit = True #для vaccuum
 
# conn.cursor will return a cursor object, you can use this cursor to perform queries
cursor = conn.cursor()



#генерируем parts из трассы и реперов
print 'генерируем parts из трассы и реперов'
cmd='ogrlineref -create -l {src_line_datasource_name} -p {src_repers_datasource_name}  -pm {pos_field_name} -o {dst_datasource_name} -s 1000'.format(
    src_line_datasource_name = src_line_datasource_name,
    src_repers_datasource_name = src_repers_datasource_name,
    pos_field_name = pos_field_name,
    dst_datasource_name = rsrc_parts_datasource_name
    )
print cmd

result = os.system(cmd)



#загружаем в postgis слой измерений
print ''
print 'Загружаем в postgis слой измерений'
import_file2postgis(measurements_layer_path,'measurements',conn_string)


#создаём новый слой 
sql = '''
DROP TABLE IF EXISTS newpointlayer CASCADE;
CREATE 
TEMPORARY
TABLE newpointlayer (
wkb_geometry geometry, 
id serial,
external_ogc_fid integer); '''
cursor.execute(sql)


#открываем слой postgis с линейными обьектами


        
#выборка фич слоя
sql = '''SELECT 
ogc_fid, 
{measurements_dist_field}::real AS dist_for_sort, 
{measurements_dist_field}::varchar AS dist 
FROM measurements 
ORDER BY dist_for_sort
'''.format(measurements_dist_field = measurements_dist_field)
cursor.execute(sql)
conn.commit()
features = cursor.fetchall()
#итерация по фичам слоя
print cursor.rowcount
bar = progressbar.ProgressBar(max_value=int(cursor.rowcount))
i=0   

for feature in features:
    bar.update(i)
    i+=1
    #if i > 100:
    #    continue

    #Запуск консольной команды, в которую передаются пути и цифры, она возвращает координаты
    cmd='ogrlineref -get_coord  -r {src_parts_datasource_name} -m {dist} '.format(
        src_parts_datasource_name = rsrc_parts_datasource_name,
         dist=feature[2],
         )
    #print cmd
    #запуск команды в системной консоли, и получение её вывода в переменную output
    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        #питоновский перехват ошибок, которые выдаёт ogrlineref, если запросить точку на пикете кратном разделению
        print e.output
        continue #переход к следующему шагу цикла for    
        
    #print output
    #как-то читаем ответ комманды
    lat,lon = ogrlineref_parse_result(output)
    #print lat,lon
    #Заносим в новый слой точку
    sql='INSERT INTO newpointlayer (wkb_geometry,external_ogc_fid) VALUES (ST_SetSRID(ST_MakePoint({lon},{lat}),{srid}), {external_ogc_fid} );'.format(
    external_ogc_fid = feature[0],
    srid=str(srid),
    lat=lat,
    lon=lon)
    #print sql
    
    #continue
    cursor.execute(sql)

    
  
#присоедниение остальных аргументов, и оно помещается в новую таблицу connections2
sql = '''
DROP TABLE IF EXISTS measurements_geo;
CREATE TABLE measurements_geo AS
SELECT 
measurements.*,
newpointlayer.wkb_geometry AS path_wkb_geometry
FROM measurements JOIN newpointlayer ON (measurements.ogc_fid = newpointlayer.external_ogc_fid);

'''
cursor.execute(sql)
'''
#Экспорт из PostGIS в Shapefile
cmd = 'ogr2ogr -f "ESRI Shapefile" -geomfield path_wkb_geometry measurements_geo.shp PG:"{conn_string}" measurements_geo '.format(conn_string=conn_string)
print cmd
os.system(cmd)
'''    
#конец

#  ogrlineref -create -l E:\MK1\DataShape\Pipe_Line_UTM.shp -p E:\MK1\DataShape\serv_UTM.shp -pm Serv -o E:\MK1\DataShape\segm_UTM.shp -s 1000 -progress --config CPL_DEBUG ON



