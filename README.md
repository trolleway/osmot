=====
### Скрипт для создания карт маршрутов общественного транспорта по данным Openstreetmap.
![sample map cropped](http://img-fotki.yandex.ru/get/9480/2107165.62/0_95e88_130b928c_orig)
Примеры карт: http://www.flickr.com/photos/trolleway/tags/osmot/

Вам потребуется PostGIS, osm2pgsql, и какой-нибудь рендер наподобие QGIS или Mapnik.
Скрипт тестировался в сборке ubuntu - osgeolive, в ней он работает из коробки.

### Использование:

* Создайте новую базу данных PostGIS.
```
createdb osmot
psql -d osmot
CREATE EXTENSION postgis;
\q
```

### Запуск примера
Укажите в файле scripts/sample/main.py параметры доступа к базе данных, и запустите 
```
python scripts/sample/main.py
```
Скрипт создаст две дополнительные таблицы в базе: "terminals_export", и "planet_osm_routes". 
planet_osm_routes - это копия таблицы planet_osm_ways, в которой добавлено поле с подписями маршрутов. Если его выводить на экран подписью линий (TextSymbolizer), то оно будет правильно указывать направление односторонних маршрутов. 

Теперь у вас есть база данных PostGIS. Далее вы можете приступать к рендерингу картинок в программе картографического рендеринга, таких как QGIS, TileMill, Mapnik, Geoserver. Я использую QGIS и TileMill. Посмотрите примеры карт: http://www.flickr.com/photos/trolleway/tags/osmot/
В QGIS вы можете добавить в проект слои terminals_export, planet_osm_routes и назначить им qml-стили, которые находятся в styles/qml.



### Подготовка osm-файла
* Отфильтруйте дамп в osmfilter, так что бы в нём остались лишь троллейбусные релейшены. Для текущей версии скрипта обязательно, что бы маршруты не выходили за границу дампа. 
```
    ./osmfilter RU-MOS.osm --keep= --keep-relations="route=trolleybus" --out-osm >RU-MOS_filtered.osm
```
Так же вы можете использовать программу osmosis с похожим синтаксисом.

### Альтернативный способ получения osm-файла с использованием JOSM 
* Установите плагин Mirrored Download 
* Установите в настройках сервер Rambler
* Скачайте всё в интересующем городе по запросу [route=trolleybus]
* Включите панель Relations, выделите все отношения с типом "Маршрут"
* Скажите "Скачать всех участников",
* Сохраните файл как .osm



