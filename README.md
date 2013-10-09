


=====
Скрипт для создания карт маршрутов общественного транспорта по данным Openstreetmap.

You need an PostGIS, osm2pgsql, and something render line QGIS or Mapnik.
Вам потребуется PostGIS, osm2pgsql, и какой-нибудь рендер наподобие QGIS или Mapnik.

Использование:

* Подготовьте osm-файл.
* Отфильтруйте дамп в osmfilter, так что бы в нём остались лишь троллейбусные релейшены. Для текущей версии скрипта обязательно, что бы маршруты не выходили за границу дампа 
* *    ./osmfilter RU-MOS.osm --keep= --keep-relations="route=trolleybus" --out-osm >RU-MOS_filtered.osm
* Альтернативный способ с использованием JOSM 
* * Установите плагин Mirrored Download 
* * Установите в настройках сервер Rambler
* * Скачайте всё в интересующем городе по запросу [route=trolleybus]
* * Включите панель Relations, выделите все отношения с типом "Маршрут"
* * Скажите "Скачать всех участников",
* * Сохраните файл как .osm
* Перейдите в рабочий каталог
* osm2pgsql -s -l -C 700 -c -d dbname -U username  RU-MOS_filtered.osm
* python osmot.py

Скрипт создаст две дополнительные таблицы в базе: "terminals", и "planet_osm_routes". 
        
planet_osm_routes - это копия таблицы planet_osm_ways, в которой добавлено поле с подписями маршрутов. Если его выводить на экран подписью линий (TextSymbolizer), то оно будет правильно указывать направление односторонних маршрутов. 

osmot
=====

Script to make public transit maps from Openstreetmap data. 
See raster samples at http://www.flickr.com/photos/trolleway/tags/osmot/

osmot means "openstreetmap" and "obshestvennyi transport" (public transport)
You need an PostGIS, osm2pgsql, and something render like QGIS or Mapnik.

Usage:

* Prepare osm-file:
* * Filter dump with osmfilter like  ./osmfilter RU-MOS.osm --keep= --keep-relations="route=trolleybus" --out-osm >RU-MOS_filtered.osm

* Go to you working directory
* osm2pgsql -s -l -C 700 -c -d dbname -U username  RU-MOS_filtered.osm
* python osmot.py

Script will created two additionaly tables in PostGIS database. The "terminals", and "planet_osm_routes". 
        TODO: replace to views
planet_osm_routes - is just a copy of planet_osm_ways, with additional field with routes refs and arrows. 
