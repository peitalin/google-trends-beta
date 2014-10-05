#!/usr/bin/env python

from distutils.core import setup

setup(name='google_trends_beta',
      version='0.9.2',
      description='Google Trends + Entity Recognition',
      author=['Peita Lin', 'D Garant'],
      author_email='peita_lin@hotmail.com',
      packages=['google_trends_beta'],
      install_requires=["argparse", "requests", "arrow", "selenium"]
     )