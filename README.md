
## Usage

0. Create PostGIS database

1. Prepare osm or pbf file with only needed routes. 

Example query for http://overpass-query.eu
```
[out:xml][timeout:25];
(
  relation["route"="bus"]["ref"!="991"]["ref"!="804"]["ref"!="833"]["ref"!="349"]["ref"!="601"](55.5396,37.6666,55.5608,37.7576);
);
out body;
>;
out meta qt;
```

2.
```
osm2pgsql --create --slim --latlon --database gis  --style d:\GIS\GIS\soft\default.style c:\Users\trolleway\Downloads\export.osm
```
3.
```
python osmot.py --user trolleway
```

4. Connect to PostGIS database in QGIS, add to map new tables: routes_with_refs and terminals_export
5. Load qml styles from /styles/qml

=====
### Скрипт для создания карт маршрутов общественного транспорта по данным Openstreetmap.
![sample map cropped](http://img-fotki.yandex.ru/get/9480/2107165.62/0_95e88_130b928c_orig)
Примеры карт: https://www.flickr.com/search/?user_id=trolleway&tags=osmot&sort=date-posted-desc

Так, пишем в readme по-русски, потому что по общественному транспорту данных в OSM мало, нужно больше местны.

Тут находится скрипт, который подготавливает сырые данные формата OSM так что по ним можно построить карту маршрутов трамваев, троллейбусов, автобусов. Так же прилагаются скрипты, которые выкачивают сырые данные, и выдают конечную картинку в png.

Скрипт тестировался под Windows и Ubuntu. И он в них работает. 
Вам потребуется PostGIS, osm2pgsql, и какой-нибудь рендер наподобие QGIS или Mapnik.

Использование под Windows:

Вы ставите СУБД PostgreSQL с плагином PostGIS. Всё это выполняется через обычный менеджер установки.
Заходите на сервер СУБД стандартной программой PgAdmin, создаёте новую базу с расширением PostGIS.
Клонируете / скачиваете этот репозиторий. В папке scripts лежит несколько разных примеров скриптов, которые выкачивают и обрабатывают Москву и Питер. 
Указываете там в конфиге логин и пароль к базе.
Ставите osm2pgsql. Вот это самое сложное под винду, надо его искать.
Рекомендуется импортировать с ключами --slim -E 3857
Запускаете скрипт. Он выкачивает транспорт города через Overpass, грузит в базу, и создаёт в ней 2 таблицы с геометриями: линии с подписями со стрелочками, и конечные пункты. 
Дальше это нужно рендрить, есть разные способы:

- Открыть эти таблицы из PostGIS в NextGIS QGIS. Стили прилагаются. Можно распечатать картинку на принтере на работе.
- В QGIS нарезать тайлы в модуле Qtiles, и загрузить тайловый слой в NextGIS Mobile на Android. Вы будете иметь карту маршрутов "в поле".
- Поставить Tilemill (объявлен устаревшим) или сырой Mapnik. Рендрить в нём маршруты и красивую подложку. Написать на питоне скрипты, которые рендрят их по-очереди, и накладывают. Пример такого скрипта - в папке с Курском.
- Показывать маршруты в вебе через NextGIS Web. Получается красиво. Демки прямо сейчас нет.

### Инструкция:

* Создайте новую базу данных PostGIS.
```
createdb osmot
psql -U username -d osmot -c "CREATE EXTENSION postgis;"
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



### Получение osm-файла с маршрутами в osmfilter
* Отфильтруйте дамп в osmfilter, так что бы в нём остались лишь троллейбусные релейшены. Для текущей версии скрипта обязательно, что бы маршруты не выходили за границу дампа. 
```
    ./osmfilter RU-MOS.osm --keep= --keep-relations="route=trolleybus" --out-osm >RU-MOS_filtered.osm
```
Так же вы можете использовать программу osmosis с похожим синтаксисом.

### Получение osm-файла с маршрутами через Overpass API
Фрагмент python-кода для использования в скриптах
```
def download_osm():
    import urllib
    #Ивановский троллейбус
    urllib.urlretrieve ('''http://overpass.osm.rambler.ru/cgi/interpreter?data=relation["route"="trolleybus"](56.917998496857315,40.89179992675781,57.06780339266955,41.119422912597656);(._;>;);out meta;''', "data.osm")

```


### Ручной способ получения osm-файла с использованием JOSM 
* Установите плагин Mirrored Download 
* Установите в настройках сервер Rambler
* Скачайте всё в интересующем городе по запросу [route=trolleybus]
* Включите панель Relations, выделите все отношения с типом "Маршрут"
* Скажите "Скачать всех участников",
* Сохраните файл как .osm




