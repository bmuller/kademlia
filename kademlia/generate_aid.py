from keri.core.coring import CryOneDex
from keri.core.coring import Ilks
from keri.core.coring import Serder
from keri.core.coring import Serials
from keri.core.coring import Signer, Nexter, Prefixer
from keri.core.coring import Versify
from keri.core.eventing import Kever
from keri.core.eventing import incept
from keri.db.dbing import openDB

# used to generate witness prefixes
def gen_nontransferable_serialized_aid():
    with openDB() as bsr:
        # Inception: Non-transferable (ephemeral) case
        signer0 = Signer(transferable=False)  #  original signing keypair non transferable
        assert signer0.code == CryOneDex.Ed25519_Seed
        assert signer0.verfer.code == CryOneDex.Ed25519N
        keys0 = [signer0.verfer.qb64]
        serder = incept(keys=keys0)  #  default nxt is empty so abandoned

        # Derive AID from ked
        aid0 = Prefixer(ked=serder.ked, code=CryOneDex.Ed25519N)

        # update ked with pre
        serder.ked["pre"] = aid0.qb64

        # Serialize ked0
        tser0 = Serder(ked=serder.ked)

        # sign serialization
        skp0 = Signer()  # original signing keypair transferable default
        tsig0 = skp0.sign(tser0.raw, index=0)

        # verify signature
        assert skp0.verfer.verify(tsig0.raw, tser0.raw)

        # not sure why this errors out when enabled; I guess kevers can't be used with nontransferable ids
        # kever = Kever(serder=tser0, sigers=[tsig0], baser=bsr)  # no error

        # return base 64 serialization of signed aid
        return tsig0.qb64


def gen_serialized_aid(witnesses):
    # taken from https://github.com/decentralized-identity/keripy/blob/6b85417ce1188543493efff48f95ebabd12fb0c6/tests/core/test_eventing.py
    with openDB() as bsr:
        # Transferable case
        # Setup inception key event dict
        # create current key
        sith = 1  #  one signer
        skp0 = Signer()  #  original signing keypair transferable default
        assert skp0.code == CryOneDex.Ed25519_Seed
        assert skp0.verfer.code == CryOneDex.Ed25519
        keys = [skp0.verfer.qb64]

        # create next key
        nxtsith = 1 #  one signer
        skp1 = Signer()  #  next signing keypair transferable is default
        assert skp1.code == CryOneDex.Ed25519_Seed
        assert skp1.verfer.code == CryOneDex.Ed25519
        nxtkeys = [skp1.verfer.qb64]
        # compute nxt digest
        nexter = Nexter(sith=nxtsith, keys=nxtkeys)
        nxt = nexter.qb64  # transferable so nxt is not empty

        sn = 0  #  inception event so 0
        toad = len(witnesses)
        nsigs = 1  #  one attached signature unspecified index

        ked0 = dict(vs=Versify(kind=Serials.json, size=0),
                    pre="",  # qual base 64 prefix
                    sn="{:x}".format(sn),  # hex string no leading zeros lowercase
                    ilk=Ilks.icp,
                    sith="{:x}".format(sith), # hex string no leading zeros lowercase
                    keys=keys,  # list of signing keys each qual Base64
                    nxt=nxt,  # hash qual Base64
                    toad="{:x}".format(toad),  # hex string no leading zeros lowercase
                    # I think these are always necessary for direct mode
                    wits=witnesses or [],  # list of qual Base64 may be empty
                    cnfg=[],  # list of config ordered mappings may be empty
                   )


        # Derive AID from ked
        aid0 = Prefixer(ked=ked0, code = CryOneDex.Ed25519)
        assert aid0.code == CryOneDex.Ed25519
        assert aid0.qb64 == skp0.verfer.qb64

        # update ked with pre
        ked0["pre"] = aid0.qb64

        # Serialize ked0
        tser0 = Serder(ked=ked0)

        # sign serialization
        tsig0 = skp0.sign(tser0.raw, index=0)

        # verify signature
        assert skp0.verfer.verify(tsig0.raw, tser0.raw)

        kever = Kever(serder=tser0, sigers=[tsig0], baser=bsr)  # no error

    
        # return base 64 serialization of signed aid
        # return tsig0.qb64
        return tsig0, tser0, tsig0.qb64