from setuptools import setup

setup (
	name			= "cmehw",
	version			= "0.1",
	description 		= "CME hardware interface",
	packages		= ['cmehw'],
	install_requires	= ["crcmod",
					"rrdtool",
					"RPi.GPIO",
					"spidev" ],
	entry_points		= {'console_scripts':
					['cmehw = cmehw.__main__:main']}
)

