TP = $(shell pwd)
VE = virtualenv
EI = $(TP)/bin/easy_install
PY = $(TP)/bin/python
PI = $(TP)/bin/pip
APPNAME = bipostal
NO = bin/nosetests --with-xunit --cover-package=$(APPNAME)

clean:
	rm -rf bipostal_storage.egg-info
	rm -rf build
	rm -rf dist

build:
	$(VE) --no-site-packages .
	bin/pip install -r dev-reqs.txt

install: 
	$(PY) setup.py install

egg: clean
	$(PY) setup.py bdist_egg --dist-dir dist

test: 
	$(NO) $(APPNAME)
