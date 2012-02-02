TP = $(shell pwd)
VE = virtualenv
EI = $(TP)/bin/easy_install
PY = $(TP)/bin/python
PI = $(TP)/bin/pip
APPNAME = bipostal
NO = bin/nosetests -s --with-xunit --cover-package=$(APPNAME)

clean:
	rm -rf bipostal_storage.egg-info
	rm -rf build
	rm -rf dist

build:
	$(VE) --no-site-packages .
	$(PI) install -r dev-reqs.txt

install: 
	$(PY) setup.py install

dist: clean build
	$(PY) setup.py sdist --dist-dir dist

test: 
	$(NO) $(APPNAME)
