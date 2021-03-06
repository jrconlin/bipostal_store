TP = $(shell pwd)
VE = virtualenv
EI = $(TP)/bin/easy_install
PY = $(TP)/bin/python
PI = $(TP)/bin/pip
APPNAME = bipostal
NO = bin/nosetests -s --with-xunit --cover-package=$(APPNAME)

build: clean setup dist

setup:
	$(VE) --no-site-packages .
	$(PI) install -r dev-reqs.txt

clean:
	rm -rf bipostal_storage.egg-info
	rm -rf build
	rm -rf dist

install: 
	$(PY) setup.py install

dist: clean build
	$(PY) setup.py sdist --dist-dir dist

test: 
	$(NO) $(APPNAME)
