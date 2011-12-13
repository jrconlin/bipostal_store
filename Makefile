TP = $(shell pwd)
VE = virtualenv
PY = $(TP)/bin/python

build:
	$(VE) --no-site-packages .

egg:
	$(PY) setup.py bdist_egg --dist-dir dist

