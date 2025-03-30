Installation
==================

The easiest (and best) way to install kademlia is through `pip <http://www.pip-installer.org/>`_::

  $ pip install kademlia
      

Usage
=====
To start a new network, create the first node.  Future nodes will connect to this first node (and any other nodes you know about) to create the network.

.. literalinclude:: ../examples/node.py

Here's an example of bootstrapping a new node against a known node and then setting a value:

.. literalinclude:: ../examples/set.py

.. note ::
    You must have at least two nodes running to store values.  If a node tries to store a value and there are no other nodes to provide redundancy, then it is an exception state.


Running Tests
=============

To run tests::

  $ pip install -r dev-requirements.txt
  $ pytest


Fidelity to Original Paper
==========================
The current implementation should be an accurate implementation of all aspects of the paper except one - in Section 2.3 there is the requirement that the original publisher of a key/value republish it every 24 hours.  This library does not do this (though you can easily do this manually).
