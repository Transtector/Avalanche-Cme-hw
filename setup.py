import os
from setuptools import setup

# version is stored in the VERSION file in package root
with open(os.path.join(os.getcwd(), 'VERSION')) as f:
	version = f.readline().strip()

setup (
	name				= "cmehw",
	version				= version,
	description			= "CME hardware/sensor interface",
	packages			= ['cmehw', 'cmehw.common'],
	install_requires	= ["crcmod", "rrdtool", "RPi.GPIO",	"spidev" ],
	entry_points		= {'console_scripts': ['cmehw = cmehw.__main__:main']}
)
