#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

PACKAGES = find_packages(exclude=['tests', 'tests.*'])


def gen_data_files(*dirs):
    results = []

    for src_dir in dirs:
        for root,dirs,files in os.walk(src_dir):
            results.append((root, map(lambda f:root + "/" + f, files)))
    return results

REQUIRES = [
    'requests>=2,<3',
    'enum-compat>=0.0.2',
    'websocket-client>=0.40.0',
    'zeroconf>=0.19.1'
]

PROJECT_CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries'
]

setup(
    name="libsoundtouch",
    version="0.7.2",
    license="Apache License 2.0",
    url="http://libsoundtouch.readthedocs.io",
    download_url="https://github.com/CharlesBlonde/libsoundtouch",
    author="Charles Blonde",
    author_email="charles.blonde@gmail.com",
    description="Bose Soundtouch Python library",
    packages=PACKAGES,
    data_files = gen_data_files("libsoundtouch/templates"),
    include_package_data=True,
    zip_safe=True,
    platforms='any',
    install_requires=REQUIRES,
    test_suite='tests',
    keywords=['bose', 'soundtouch'],
    classifiers=PROJECT_CLASSIFIERS,
)
