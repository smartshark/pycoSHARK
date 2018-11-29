#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

import pycoshark

setup(
    name='pycoSHARK',
    version=pycoshark.__version__,
    description='Basic MongoDB Models for smartSHARK.',
    install_requires=['mongoengine', 'pymongo'],
    author='ftrautsch',
    author_email='fabian.trautsch@uni-goettingen.de',
    url='https://github.com/smartshark/pycoSHARK',
    download_url='https://github.com/smartshark/pycoSHARK/zipball/master',
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
