.. Kademlia documentation master file, created by
   sphinx-quickstart on Mon Jan  5 09:42:46 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Kademlia Documentation
======================

.. note ::
    This library assumes you have a working familiarity with Twisted_.

This library is an asynchronous Python implementation of the `Kademlia distributed hash table <http://en.wikipedia.org/wiki/Kademlia>`_.  It uses Twisted_ to provide asynchronous communication.  The nodes communicate using `RPC over UDP <https://github.com/bmuller/rpcudp>`_ to communiate, meaning that it is capable of working behind a `NAT <http://en.wikipedia.org/wiki/NAT>`_.

This library aims to be as close to a reference implementation of the `Kademlia paper <http://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf>`_ as possible.

.. _Twisted: https://twistedmatrix.com

.. toctree::
   :maxdepth: 3
   :titlesonly:

   intro
   querying
   source/modules
   
	      
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

