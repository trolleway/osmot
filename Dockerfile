
RUN mkdir osmtram_preprocessing
RUN chmod  --recursive 777 /osmtram_preprocessing

RUN mkdir /osmtram_preprocessing/volumedata
WORKDIR /osmtram_preprocessing

RUN git clone --recurse-submodules https://github.com/trolleway/OSMTram.git 

# Создание конфигов с захардкодеными адресами
COPY configs4docker/.pgpass /routing_preprocessing/.pgpass
COPY configs4docker/config.cfg /routing_preprocessing/config.cfg
COPY configs4docker/osmosis_creds.cfg /routing_preprocessing/osmosis_creds.cfg

# Проброс скриптов с кодом (решили не использовать git, у нас же закрытый реп)
COPY check_db.sh /routing_preprocessing/check_db.sh
COPY pgsnapshot_schema_0.6.sql /routing_preprocessing/pgsnapshot_schema_0.6.sql
COPY level1_helpers.sql /routing_preprocessing/level1_helpers.sql
COPY level2_split.sql /routing_preprocessing/level2_split.sql
COPY level3_join_user_highways.sql /routing_preprocessing/level3_join_user_highways.sql

COPY process.sh /routing_preprocessing/process.sh

#debug software
#RUN apt-get install -y less


#ENTRYPOINT ["/routing_preprocessing/check_db.sh"]
CMD ["/bin/bash" , "/osmtram_preprocessing/indocker.sh"]
