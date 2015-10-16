#!/usr/bin/env python
from setuptools import setup, find_packages
from kademlia import version

setup(
    name="kademlia",
    version=version,
    description="Kademlia is a distributed hash table for decentralized peer-to-peer computer networks.",
    long_description=open("README.markdown").read(),
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    test_suite="kademlia.tests",
    url="http://github.com/bmuller/kademlia",
    packages=find_packages(),
    install_requires=open("requirements.txt").readlines(),
    tests_require=open("test_requirements.txt").readlines(),
    classifiers=[
        # "Development Status :: 1 - Planning",
        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
