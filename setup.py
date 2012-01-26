#!env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup

setup(
    name='bipostal_storage',
    version='0.2',
    description='Shared storage for bipostal* functions',
    author='JR Conlin',
    author_email='jrconlin+bipostal@mozilla.org',
    packages=['bipostal', 'bipostal.storage'],
    long_description=""""
    Common storage library for BIPostal
    """,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Development Status :: 2 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet"],
    keywords='Mozilla Services BIPostal',
    license='BSD',
    install_requires=['redis', 
        'DBUtils', 
        'python_memcached', 
        'mysql_python'],
)

