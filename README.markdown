# Python Distributed Hash Table
[![Build Status](https://secure.travis-ci.org/bmuller/kademlia.png?branch=master)](https://travis-ci.org/bmuller/kademlia)
[![Docs Status](https://readthedocs.org/projects/kademlia/badge/?version=latest)](http://kademlia.readthedocs.org)

**Documentation can be found at [kademlia.readthedocs.org](http://kademlia.readthedocs.org/).**

This library is an asynchronous Python implementation of the [Kademlia distributed hash table](http://en.wikipedia.org/wiki/Kademlia).  It uses [Twisted](https://twistedmatrix.com) to provide asynchronous communication.  The nodes communicate using [RPC over UDP](https://github.com/bmuller/rpcudp) to communiate, meaning that it is capable of working behind a [NAT](http://en.wikipedia.org/wiki/NAT).

This library aims to be as close to a reference implementation of the [Kademlia paper](http://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) as possible.

## Installation

```
pip install kademlia
```

## Usage
*This assumes you have a working familiarity with [Twisted](https://twistedmatrix.com).*

Assuming you want to connect to an existing network (run the standalone server example below if you don't have a network):

```python
from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

# log to std out
log.startLogging(sys.stdout)

def quit(result):
    print "Key result:", result
    reactor.stop()

def get(result, server):
    return server.get("a key").addCallback(quit)

def done(found, server):
    log.msg("Found nodes: %s" % found)
    return server.set("a key", "a value").addCallback(get, server)

server = Server()
# next line, or use reactor.listenUDP(5678, server.protocol)
server.listen(5678)
server.bootstrap([('127.0.0.1', 1234)]).addCallback(done, server)

reactor.run()
```

Check out the examples folder for other examples.

## Stand-alone Server
If all you want to do is run a local server, just start the example server:

```
twistd -noy examples/server.tac
```

## Web Server Server
In order to have a simple web server, you only need to execute the web-server that is available in the examples directory:

```
twistd -noy examples/webserver.tac
```

In this example, it is possible to POST and GET data to/from the DHT, as well as get information about the known neighbors of this peer.

Post data to DHT:
```
curl --data "hi there" http://localhost:8080/dht/one
```

Get data from DHT:
```
curl http://localhost:8080/dht/one
```

Get neighbors:
```
curl http://localhost:8080/neighbours
```

## Distributed Environment Example

With the aim of providing a basic example of a DHT network, it is available in the examples directory 3 peers source code examples (based on webserver), as well as the configuration of Virtual Machines to deploys these peer webservers (using [Vagrant](https://www.vagrantup.com/)) in a simple and fast way.

```
Peer1 --> 192.168.33.10 (8468)
Peer2 --> 192.168.33.11 (8469)
Peer3 --> 192.168.33.12 (8470)
```

Then, it is only necessary to execute the same commands as the Web Server section, changing the IP address.

## Running Tests
To run tests:

```
trial kademlia
```


## Fidelity to Original Paper
The current implementation should be an accurate implementation of all aspects of the paper save one - in Section 2.3 there is the requirement that the original publisher of a key/value republish it every 24 hours.  This library does not do this (though you can easily do this manually).
