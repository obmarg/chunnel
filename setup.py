#!/usr/bin/env python

from setuptools import setup, find_packages

REQUIREMENTS = ['websockets']
LONG_DESCRIPTION = '''
Chunnel
-----

A python client for phoenix channels.

See the README at https://github.com/obmarg/chunnel for more details.

'''

setup(
    name='chunnel',
    version='0.1.0',
    url='https://github.com/obmarg/chunnel',
    description='Phoenix channels client library',
    long_description=LONG_DESCRIPTION,
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
