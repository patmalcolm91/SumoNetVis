from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
  name='SumoNetVis',
  packages=['SumoNetVis'],
  version='1.5.0',
  license='MIT',
  description='A python library to render Sumo network files and trajectories with matplotlib or as an OBJ file.',
  long_description=long_description,
  long_description_content_type='text/markdown',
  author='Patrick Malcolm',
  author_email='patmalcolm91@gmail.com',
  url='https://github.com/patmalcolm91/SumoNetVis',
  download_url='https://github.com/patmalcolm91/SumoNetVis/archive/v1.5.0.tar.gz',
  keywords=['sumo', 'network', 'visualize', 'plot', 'matplotlib', 'traffic'],
  install_requires=[
          'shapely',
          'matplotlib',
          'numpy'
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8'
  ]
)
