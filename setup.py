#!/usr/bin/env python
from setuptools import setup, find_packages
from kademlia import version

setup(
    name="kademlia",
    version=version,
    description="Kademlia is a distributed hash table for decentralized peer-to-peer computer networks.",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://github.com/bmuller/kademlia",
    packages=find_packages(),
    requires=["twisted", "rpcudp", "PyNaCl"],
    install_requires=['twisted>=14.0', "rpcudp>=1.0", "PyNaCl>=0.3.0"]
)
