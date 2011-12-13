#!env python

from setuptools import setup

setup(
    name='bipostal_storage',
    version='0.1',
    description='Shared storage for bipostal* functions',
    author='JR Conlin',
    author_email='jrconlin+bipostal@mozilla.org',
    packages=['bipostal.storage'],
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
        'DBUtils.SimplePooledDB', 
        'memcache', 
        'MySQLdb'],
)

