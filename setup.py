#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='upay',
    version='1.0.0',
    description='Rewrite of upay',
    author='Tobias Schneider',
    author_email='schneider@xtort.eu',
    url='https://github.com/muccc/upay',
    packages=['upay'],
    scripts=['scripts/mqtt-git-forwarder', 'scripts/mqtt-mail-forwarder'],
    long_description=open('README.md').read(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or ",
        "later (GPLv3+)",
        "Programming Language :: Python :: 2",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    requires=["jsonschema", "requests", "iso8601", "pygit", "mosquitto"],
    keywords='upay',
    license='GPLv3+',
)
