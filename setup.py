#!/usr/bin/env python

from distutils.core import setup

setup(name='google_trends',
      version='0.5',
      description='Batch Querying Tool for Google Trends',
      author=['Dan Garant','Peita Lin']
      author_email='dgarant@cs.umass.edu',
      packages=['google_trends_beta'],
      install_requires=["argparse", "requests", "arrow", "fuzzywuzzy", "selenium", "clint", "phantomjs"]
     )
