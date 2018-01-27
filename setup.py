#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2018 Simon Forman
#
#    This file is part of joy.py
#
#    joy.py is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    joy.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with joy.py.  If not see <http://www.gnu.org/licenses/>.
#
from setuptools import setup
from textwrap import dedent


setup(
  name='Joypy_GUI',
  version='0.1',
  description='GUI for Joy',
  long_description=dedent('''\
    Etc... blah blah'''),
  author='Simon Forman',
  author_email='forman.simon@gmail.com',
  url='https://github.com/calroc/joypy_gui',
  packages=['gui'],
  entry_points={'console_scripts': ['gui_joy=gui.main:main']},
  classifiers=[
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python :: 2.7',
    ],
  )
