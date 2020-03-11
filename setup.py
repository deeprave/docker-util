# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='docker-util',
    version='2018.03.11',
    license='Apache 2',
    author='David Nugent',
    author_email='davidn@uniquode.io',
    description='Docker command line utility',
    url='https://github.com/deeprave/docker-util',
    packages=[],
    install_requires=[
        'docker',
    ],
    scripts=[
        'src/dockerutil.py'
    ]
)
