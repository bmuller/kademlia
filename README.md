# Python Distributed Hash Table
[![Build Status](https://github.com/bmuller/kademlia/actions/workflows/ci.yml/badge.svg)](https://github.com/bmuller/kademlia/actions/workflows/ci.yml)
[![Docs Status](https://readthedocs.org/projects/kademlia/badge/?version=latest)](http://kademlia.readthedocs.org)

**Documentation can be found at [kademlia.readthedocs.org](http://kademlia.readthedocs.org/).**

This library is an asynchronous Python implementation of the [Kademlia distributed hash table](http://en.wikipedia.org/wiki/Kademlia).  It uses the [asyncio library](https://docs.python.org/3/library/asyncio.html) in Python 3 to provide asynchronous communication.  The nodes communicate using [RPC over UDP](https://github.com/bmuller/rpcudp) to communiate, meaning that it is capable of working behind a [NAT](http://en.wikipedia.org/wiki/Network_address_translation).

This library aims to be as close to a reference implementation of the [Kademlia paper](http://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) as possible.

## Installation

```
pip install kademlia
```

## Usage
*This assumes you have a working familiarity with [asyncio](https://docs.python.org/3/library/asyncio.html).*

Assuming you want to connect to an existing network:

```python
import asyncio
from kademlia.network import Server

async def run():
    # Create a node and start listening on port 5678
    node = Server()
    await node.listen(5678)

    # Bootstrap the node by connecting to other known nodes, in this case
    # replace 123.123.123.123 with the IP of another node and optionally
    # give as many ip/port combos as you can for other nodes.
    await node.bootstrap([("123.123.123.123", 5678)])

    # set a value for the key "my-key" on the network
    await node.set("my-key", "my awesome value")

    # get the value associated with "my-key" from the network
    result = await node.get("my-key")
    print(result)

asyncio.run(run())
```

## Initializing a Network
If you're starting a new network from scratch, just omit the `node.bootstrap` call in the example above.  Then, bootstrap other nodes by connecting to the first node you started.

See the examples folder for a first node example that other nodes can bootstrap connect to and some code that gets and sets a key/value.

## Logging
This library uses the standard [Python logging library](https://docs.python.org/3/library/logging.html).  To see debut output printed to STDOUT, for instance, use:

```python
import logging

log = logging.getLogger('kademlia')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
```

## Running Tests
To run tests:

```
uv sync --dev
uv run pytest
```

## Reporting Issues
Please report all issues [on github](https://github.com/bmuller/kademlia/issues).

## Fidelity to Original Paper
The current implementation should be an accurate implementation of all aspects of the paper save one - in Section 2.3 there is the requirement that the original publisher of a key/value republish it every 24 hours.  This library does not do this (though you can easily do this manually).
