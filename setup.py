#!/usr/bin/env python

from setuptools import setup, find_packages

REQUIREMENTS = ['websockets']

setup(
    name='chunnel',
    version='0.1.0',
    description='Phoenix channels client library',
    author='Graeme Coupar',
    author_email='grambo@grambo.me.uk',
    packages=find_packages(exclude=['tests']),
    install_requires=REQUIREMENTS,
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5'
    ]
)
