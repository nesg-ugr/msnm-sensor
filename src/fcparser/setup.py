# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='fcparser',
      version='1.0.0',
      description='Feature as a Counter Parser',
      url='https://github.com/josecamachop/FCParser',
      author='Alejandro Perez Villegas, Jose Manuel Garcia Gimenez, José Camacho Páez',
      author_email='alextoni@gmail.com, jgarciag@ugr.es, josecamacho@ugr.es',
      license='GPLv3',
      packages=['fcparser','deparser'],
      install_requires=[
          'IPy', 'pyyaml'
      ],
      zip_safe=False)
