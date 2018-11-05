FROM python:3.6-slim-stretch

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
 && apt-get -y upgrade \
 && apt-get -yq --allow-unauthenticated install --no-install-recommends libgdal20 \
 && apt-get clean \
 && rm -fr /var/lib/apt/lists/*

RUN apt-get update \
 && apt-get -yq --allow-unauthenticated install --no-install-recommends gcc g++ libgdal-dev \
 && pip install --no-cache --global-option=build_ext --global-option="-I/usr/include/gdal" 'gdal<2.2' \
 && pip install --no-cache netCDF4 pydap PasteScript pyramid waitress gunicorn \
 && pip install --no-cache https://github.com/geopython/pywps/archive/699457de2da67796008e8529edea4b6e52b7ea99.zip \
 && apt-get -y purge gcc g++ libgdal-dev \
 && apt -y autoremove \
 && apt-get clean \
 && rm -fr /var/lib/apt/lists/*

RUN pip install --no-cache https://github.com/ausecocolud/ecocloud_wps_demo/aa8945d4b8d217c4c0a644b940532762751a920e.zip

COPY pywps.cfg /etc/ecocloud/pywps.cfg
COPY development.ini /etc/ecocloud/wps.ini

CMD ["paster", "serve", "/etc/ecocloud/wps.ini", "--reload"]
