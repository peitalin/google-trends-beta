#!/usr/bin/env python

from distutils.core import setup

setup(name='google_trends_beta',
<<<<<<< HEAD
      version='0.9.2',
      description='Google Trends + Entity Recognition',
      author=['Peita Lin', 'D Garant'],
=======
      version='0.9',
      description='Google Trends + Entity Recognition',
      author=['Peita Lin', 'Dan Garant'],
>>>>>>> cbb54418f3e864e560b97e001f95061ffbb3a12b
      author_email='peita_lin@hotmail.com',
      packages=['google_trends_beta'],
      install_requires=["argparse", "requests", "arrow", "selenium", "colorama"]
     )
