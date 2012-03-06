# Installation:

## Pre-requisites:

* git

* svn

* nginx

* Python 2.6

* python-devel

* python-virtualenv

* gcc

* make

* mysql\_server

* PostFix (or any other milter compatible MTA)

## Installation:

1. $ make build

2. copy the 

3. copy and modify the *-dist.ini files to match your configuration

4. Execute the following scripts (you may wish to run them in screen):

 bin/python src/bipostmap.py --config=src/bipostmap.ini

 bin/python src/bipostal_milter.py --config=src/bipostal_milter.ini

5. modify the /etc/postfix/main.cf file and include the following lines:

 canonical_maps = tcp:localhost:9998
 smtpd_milters  = inet:localhost:9999
 non_smtpd_milters = inet:localhost:9999

Please modify as appropriate.

6. Restart postfix 
