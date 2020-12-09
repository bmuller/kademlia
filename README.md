# Keridemlia: Discovery Mechanism for KERI using Kademlia

[KERI](https://github.com/decentralized-identity/keri) is an end-to-end identity system for the Interjnet that places the primary root-of-trust in self-certifying Autonomic Identifiers (AIDs). Running KERI in indirect mode requires users or controllers to know mappings of AIDs to witness IP addresses in order to communicate and verify identities. Keridemlia solves this problem by providing a discovery mechanism that maps AIDs to witness IDs and witness IDs to witness IPs. This is done using a Distributed Hash Table, Kademlia.

## API

```buildoutcfg
1. POST /id/<aid>/<witness_id>             (publish AID -> ID mapping)
2. GET  /id<aid>                           (get witness ID from AID)
3. POST /ip/<witness_id>/<witness_ip>      (publish ID -> IP mapping)
4. GET  /ip/<witness_id>                   (get witness IP from witness IP)
```

## Running

To bootstrap a new Kademlia cluster (rather than joining an existing one), first run:
```
python3 bootstrap.py
```

Then in another terminal, to get the actual API, run:
```
python3 primary.py
```

## TODO

Keridemlia is in initial stages of development. Verification is supposed to happen before data is published to the DHT, but this has not been figured out yet. Because of this, the id/ip APIs are disabled and the aid/id APIs work without verification.

After verification is complete and all APIs are working, next steps might include local caching for further optimizations, as well as an signed IP address type to store for id/ip APIs.
