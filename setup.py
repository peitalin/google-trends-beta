#!/usr/bin/env python

from distutils.core import setup

setup(name='google_trends',
      version='1.0',
      description='Batch Querying Tool for Google Trends',
      author='Dan Garant',
      author_email='dgarant@cs.umass.edu',
      packages=['google_trends'],
      install_requires=["argparse", "requests", "arrow"]
     )
