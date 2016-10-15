#!/usr/bin/python2.7

"""
	setup module for busfactor
	
	See:
	https://github.com/SOM-Research/busfactor/
	
	https://packaging.python.org/en/latest/distributing.html
	https://github.com/pypa/sampleproject
"""

from distutils.core import setup

setup(name='busfactor',
	version='0.2',
	license='MIT',
	author='valerio cosentino',
	url='https://github.com/SOM-Research/busfactor',
	description='A bus factor analyzer for Git repositories',
	long_description='A bus factor analyzer for Git repositories.',
	keywords='Busfactor: Bus factor analyzer Git repositoriesr',
	packages=['busfactor'],
	package_dir={'busfactor': ''},
	package_data={'busfactor': ['css/*.css', 'css/bootstrap/*.css',
							 'data/*.json', 'js/*.js', 'js/bootstrap/*.js',
							 'js/vendor/*.js', '*.png', 'index.html, 
							 'LICENSE']},
)
