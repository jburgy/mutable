# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='mutable',
    version='0.1.0',
    description='Consistent mutable cache',
    long_description=readme,
    author='Jan Burgy',
    author_email='jburgy@gmail.com',
    url='https://github.com/jburgy/mutable',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
