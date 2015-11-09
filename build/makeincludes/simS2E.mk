### TODO
### FAST database interface

###################
#     WPG/SRW     #
###################
#include ${ROOT_DIR}/packages/environment.mk

default: all

all: build\
   	install

fetch:
	cd ${PACKAGES} && \
	wget http://github.com/samoylv/WPG/archive/develop.zip -O wpg-develop.zip && \
	wget https://github.com/samoylv/prop/archive/develop.zip -O prop-develop.zip

unpack:
	cd ${SRC} && \
	unzip -o ${PACKAGES}/wpg-develop.zip && \
	unzip -o ${PACKAGES}/prop-develop.zip

patch: unpack
	cd ${SRC}/prop-develop && \
	patch propagateSE.py ${PATCHES}/wpg/propagateSE.py.patch && \
	patch diagnostics.py ${PATCHES}/wpg/diagnostics.py.patch

build: patch
	cd ${SRC}/WPG-develop && make all

install:
	cd ${SRC} && \
	cp -r prop-develop ${LIB}/prop && \
	cp -r WPG-develop/wpg ${LIB}
	cd ${ROOT}/python && \
	ln -s ../lib lib && \
	cd ${LIB}/prop && \
	touch __init__.py


# Pull zipped repository from github.
# Unpack
# Patch
# Build
# Install
