osmot
=====

Script to make public transit maps from Openstreetmap data

Usage:

1.      Подготовьте osm-файл. 
        1.1.    Отфильтруйте дамп в osmfilter, так что бы в нём остались лишь троллейбусные релейшены, или
        1.2.    Запустите JOSM
                Установите плагин Mirrored Download
                Установите сервер Rambler
                Скачайте всё в интересующем городе по запросу [route=trolleybus]
                Включите панель Relations, выделите все отношения с типом "Маршрут" и скажите "Скачать всех участников"
                Сохраните файл как .osm
2.      Go to you working directory
3.      osm2pgsql -s -l -C 700 -c -d dbname -U username  city_trolleybus_lines.osm
4.      python osmot.py

Script will created two additionaly tables in PostGIS database. The "terminals", and "planet_osm_routes". 
        TODO: replace to views
planet_osm_routes - is just a copy of planet_osm_ways, with additional field with routes refs and arrows. The way geometry in some records are backwarded (я забыл, зачем это надо было). 
