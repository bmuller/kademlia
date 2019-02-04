#!/usr/bin/env python
from setuptools import setup, find_packages
import kademlia

setup(
    name="kademlia",
    version=kademlia.__version__,
    description="Kademlia is a distributed hash table for decentralized peer-to-peer computer networks.",
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://github.com/bmuller/kademlia",
    packages=find_packages(),
    install_requires=open("requirements.txt").readlines(),
    classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.5",
      "Programming Language :: Python :: 3.6",
      "Programming Language :: Python :: 3.7",
      "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
