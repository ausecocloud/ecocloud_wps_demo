# Docker image for ecocloud WPS demo

### Python 3.6 with Debian `buster` ###

FROM buildpack-deps:buster

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# extra dependencies (over what buildpack-deps already includes)
RUN apt-get update && apt-get install -y --no-install-recommends \
		tk-dev \
	&& rm -rf /var/lib/apt/lists/*

ENV GPG_KEY 0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D
ENV PYTHON_VERSION 3.6.7

RUN set -ex \
	\
	&& wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& { command -v gpgconf > /dev/null && gpgconf --kill all || :; } \
	&& rm -rf "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz \
	\
	&& cd /usr/src/python \
	&& gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
	&& ./configure \
		--build="$gnuArch" \
		--enable-loadable-sqlite-extensions \
		--enable-shared \
		--with-system-expat \
		--with-system-ffi \
		--without-ensurepip \
	&& make -j "$(nproc)" \
	&& make install \
	&& ldconfig \
	\
	&& find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' + \
	&& rm -rf /usr/src/python \
	\
	&& python3 --version

# make some useful symlinks that are expected to exist
RUN cd /usr/local/bin \
	&& ln -s idle3 idle \
	&& ln -s pydoc3 pydoc \
	&& ln -s python3 python \
	&& ln -s python3-config python-config

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 18.1

RUN set -ex; \
	\
	wget -O get-pip.py 'https://bootstrap.pypa.io/get-pip.py'; \
	\
	python get-pip.py \
		--disable-pip-version-check \
		--no-cache-dir \
		"pip==$PYTHON_PIP_VERSION" \
	; \
	pip --version; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py

### WPS demo content ###

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
 && apt-get -y upgrade \
 && apt-get -yq --allow-unauthenticated install --no-install-recommends libgdal20 \
 && apt-get clean \
 && rm -fr /var/lib/apt/lists/*

RUN apt-get update \
 && apt-get -yq --allow-unauthenticated install --no-install-recommends gcc g++ libgdal-dev \
 && pip install --no-cache --global-option=build_ext --global-option="-I/usr/include/gdal" 'gdal==2.3.*' \
 && pip install --no-cache netCDF4==1.3.1 pydap PasteScript pyramid waitress gunicorn \
 && pip install --no-cache https://github.com/geopython/pywps/archive/699457de2da67796008e8529edea4b6e52b7ea99.zip \
 && pip install --no-cache https://github.com/NCPP/ocgis/archive/b00dd591df47467fabe5f9894cc7ab3e6e209bf0.zip \
 && apt-get -y purge gcc g++ libgdal-dev \
 && apt -y autoremove \
 && apt-get clean \
 && rm -fr /var/lib/apt/lists/*

# RUN pip install --no-cache https://github.com/ausecocloud/ecocloud_wps_demo/archive/f09b87fe0431b56c8ad29c362f4e82d61683958e.zip
RUN pip install --no-cache https://github.com/manhinli/ecocloud_wps_demo/archive/f09b87fe0431b56c8ad29c362f4e82d61683958e.zip

COPY pywps.cfg /etc/ecocloud/pywps.cfg
COPY development.ini /etc/ecocloud/wps.ini

ENV GDAL_DATA /usr/share/gdal

CMD ["paster", "serve", "/etc/ecocloud/wps.ini", "--reload"]
