#!/usr/bin/env python

from flickrSync import __ver__
try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name="flickrSync",
	version=__ver__,
	description="Python Flickr photo synchronization using OAuth",
	long_description=open("README.md").read(),
	author="Tomáš Souček",
	author_email="soucek.gns@gmail.com",
	url="https://github.com/soCzech",
	packages=[
		"flickrSync"
	],
	license="LICENSE.txt",
	install_requires=[
		"requests >= 2.2.0"
	],
)
