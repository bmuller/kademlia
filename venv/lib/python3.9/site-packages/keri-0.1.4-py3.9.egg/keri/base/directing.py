# -*- encoding: utf-8 -*-
"""
KERI
keri.demo.directing module

simple direct mode demo support classes
"""
from hio.base import doing, tyming
from hio.core.tcp import clienting, serving
from .. import kering
from ..db import dbing
from ..core import coring, eventing


class Habitat():
    """
    Habitat class provides direct mode controller's local shared habitat
       e.g. context or environment

     Attributes:
        .secrets is list of secrets (replace later with keeper interface)
        .kevers is dict of Kevers keyed by qb64 prefix
        .db is s lmdb db Baser instance
        .signers is dict  of signers for each secret indexed by verfer qb64
        .inception is Serder of inception event
        .pre is qb64 prefix of local controller
    """
    def __init__(self, secrets, kevers, db):
        """
        Initialize instance.

        Parameters:
            secrets is list of secrets (replace later with keeper interface)
            kevers is dict of Kever instance keyed by qb64 prefix
            db is lmdb db Baser instance
        """
        self.secrets = secrets
        self.kevers = kevers
        self.db = db
        self.signers = [coring.Signer(qb64=secret) for secret in self.secrets]
        self.inception = eventing.incept(keys=[self.signers[0].verfer.qb64],
                        nxt=coring.Nexter(keys=[self.signers[1].verfer.qb64]).qb64,
                        code=coring.CryOneDex.Blake3_256)
        self.pre = self.inception.ked['pre']


class Director(doing.Doer):
    """
    Direct Mode KERI Director (Contextor, Doer) with TCP Client and Kevery
    Generator logic is to iterate through initiation of events for demo

    Inherited Attributes:

    Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP client instance. Assumes operated by another doer.
        .kevery is Kevery instance

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, hab, client,  **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock

        Parameters:
            hab is Habitat instance
            client is TCP Client instance

        """
        super(Director, self).__init__(**kwa)
        self.hab = hab
        self.client = client  #  use client for tx only
        self.kevery = eventing.Kevery(kevers=self.hab.kevers,
                                      baser=self.hab.db)


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send


        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration


class Reactor(doing.Doer):
    """
    Direct Mode KERI Reactor (Contextor, Doer) class with TCP Client and Kevery
    Generator logic is to react to events/receipts from remote Reactant with receipts

    Inherited Attributes:

    Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP Client instance.
        .kevery is Kevery instance

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, hab, client,  **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock

        Parameters:
            hab is Habitat instance of local controller's context
            client is TCP Client instance
        """
        super(Reactor, self).__init__(**kwa)
        self.hab = hab
        self.client = client  #  use client for both rx and tx
        self.kevery = eventing.Kevery(ims=self.client.rxbs,
                                      kevers=self.hab.kevers,
                                      baser=self.hab.db,
                                      framed=False)


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                self.service()



        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration


    def service(self):
        """
        Service responses
        """
        if self.kevery:
            if self.kevery.ims:
                print("{} received:\n{}\n\n".format(self.hab.pre, self.kevery.ims))
            self.kevery.processAll()
            self.processCues()


    def processCues(self):
        """
        Process all cues in .kevery
        """
        while self.kevery.cues:  # process any cues
            # process each cue
            cue = self.kevery.cues.popleft()
            print("{} sent cue:\n{}\n\n".format(self.hab.pre, cue))
            self.processCue(cue=cue)


    def processCue(self, cue):
        """
        Process a cue in direct mode assumes chits
        """
        cuePre = cue["pre"]
        cueSerder = cue["serder"]
        cueKed = cueSerder.ked
        cueIlk = cueKed["ilk"]

        if cueIlk == coring.Ilks.icp:
            # check for chit from remote pre for own inception
            dgkey = dbing.dgKey(self.hab.pre, self.hab.inception.dig)
            found = False
            for triplet in self.hab.db.getVrcsIter(dgkey):
                if bytes(triplet).decode("utf-8").startswith(cuePre):
                    found = True
                    break

            if not found:  # no chit from remote so send own inception
                self.sendOwnInception()

        self.sendOwnChit(cuePre, cueSerder)


    def sendOwnChit(self, cuePre, cueSerder):
        """
        Send chit of event indicated by cuePre and cueSerder
        """
        # send own chit of event
        # create seal of own last est event
        kever = self.hab.kevers[self.hab.pre]
        seal = eventing.SealEvent(pre=self.hab.pre,
                                  dig=kever.lastEst.dig)

        cueKed = cueSerder.ked
        # create validator receipt
        reserder = eventing.chit(pre=cuePre,
                                 sn=int(cueKed["sn"], 16),
                                 dig=cueSerder.dig,
                                 seal=seal)
        # sign cueSerder event not receipt
        counter = coring.SigCounter(count=1)
        # use signer that matcher current verfer  # not multisig
        verfer = kever.verfers[0]
        siger = None
        for signer in self.hab.signers:
            if signer.verfer.qb64 == verfer.qb64:
                siger = signer.sign(ser=cueSerder.raw, index=0)  # return Siger if index
                break
        if siger:
            # process own chit so have copy in own log
            msg = bytearray(reserder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)
            self.kevery.processOne(ims=bytearray(msg), framed=True)  # make copy

            # send to remote
            self.client.tx(bytes(msg))  #  make copy because tx uses deque
            print("{} sent chit:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]


    def sendOwnInception(self):
        """
        Utility to send own inception on client
        """
        # send own inception
        esn = 0
        counter = coring.SigCounter()  # default is count = 1
        # sign serialization, returns Siger if index provided
        siger = self.hab.signers[esn].sign(self.hab.inception.raw, index=0)
        #  create serialized message
        msg = bytearray(self.hab.inception.raw)
        msg.extend(counter.qb64b)
        msg.extend(siger.qb64b)

        # check valid by creating own Kever using own Kevery
        #self.kevery.processOne(ims=bytearray(msg))  # copy of msg
        #kever = self.kevery.kevers[self.hab.pre]
        #assert kever.prefixer.qb64 == self.hab.pre

        # send to connected remote
        self.client.tx(bytes(msg))  # make copy for now fix later
        print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
        del msg[:]  #  clear msg


class Directant(doing.Doer):
    """
    Direct Mode KERI Directant (Contextor, Doer) class with TCP Server
    Logic is to respond to initiated events by remote Director by running
    a Reactant per connection.

    Inherited Attributes:

    Attributes:
        .hab is Habitat instance of local controller's context
        .server is TCP client instance. Assumes operated by another doer.
        .rants is dict of Reactants indexed by connection address

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, hab, server,  **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock

        Parameters:
            hab is Habitat instance of local controller's context
            server is TCP Server instance
        """
        super(Directant, self).__init__(**kwa)
        self.hab = hab
        self.server = server  #  use server for cx
        self.rants = dict()


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                self.serviceConnects()
                self.serviceRants()


        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration


    def closeConnection(self, ca):
        """
        Close and remove connection given by ca
        """
        if ca in self.rants:
            del self.rants[ca]
        if ca in self.server.ixes:  #  incomer still there
            self.server.ixes[ca].serviceTxes()  #  send final bytes to socket
        self.server.removeIx(ca)


    def serviceConnects(self):
        """
        New connections get Reactant added to .rants
        """
        for ca, ix in list(self.server.ixes.items()):
            if ix.cutoff:
                self.closeConnection(ca)
                continue

            if ca not in self.rants:  # create Reactant
                self.rants[ca] = Reactant(hab=self.hab, incomer=ix)

            if ix.timeout > 0.0 and ix.tymer.expired:
                self.closeConnection(ca)

    def serviceRants(self):
        """
        Service pending reactants
        """
        for ca, reactant in self.rants.items():
            if reactant.kevery:
                if reactant.kevery.ims:
                    print("{} received:\n{}\n\n".format(self.hab.pre, reactant.kevery.ims))

                reactant.kevery.processAll()
                reactant.processCues()

            if not reactant.persistent:  # not persistent so close and remove
                ix = self.server.ixes[ca]
                if not ix.txes:  # wait for outgoing txes to be empty
                    self.closeConnection(ca)



class Reactant(tyming.Tymee):
    """
    Direct Mode KERI Reactant (Contextor) class with TCP Incomer and Kevery
    Purpose is to react to received events from remote Director with receipts/events

    Inherited Attributes:

    Attributes:
        .hab is Habitat instance of local controller's context
        .incomer is TCP Incomer instance.
        .kevery is Kevery instance
        .persistent is boolean, True means keep connection open. Otherwise close

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time

    Properties:

    Inherited Methods:

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
    """

    def __init__(self, hab, incomer,  persistent =True, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance

        Parameters:
            hab is Habitat instance of local controller's context
            incomer is TCP Incomer instance
        """
        super(Reactant, self).__init__(**kwa)
        self.hab = hab
        self.incomer = incomer  #  use incomer for both rx and tx
        self.kevery = eventing.Kevery(ims=self.incomer.rxbs,
                                      kevers=self.hab.kevers,
                                      baser=self.hab.db,
                                      framed=False)
        self.persistent = True if persistent else False


    def processCues(self):
        """
        Process any cues in .kevery
        """

        while self.kevery.cues:  # process any cues
            # process each cue
            cue = self.kevery.cues.popleft()
            print("{} sent cue:\n{}\n\n".format(self.hab.pre, cue))
            self.processCue(cue=cue)


    def processCue(self, cue):
        """
        Process a cue in direct mode assumes chits
        """
        cuePre = cue["pre"]
        cueSerder = cue["serder"]
        cueKed = cueSerder.ked
        cueIlk = cueKed["ilk"]

        if cueIlk == coring.Ilks.icp:
            # check for chit from remote pre for own inception
            dgkey = dbing.dgKey(self.hab.pre, self.hab.inception.dig)
            found = False
            for triplet in self.hab.db.getVrcsIter(dgkey):
                if triplet.startswith(bytes(cuePre)):
                    found = True
                    break

            if not found:  # no chit from remote so send own inception
                self.sendOwnInception()

        self.sendOwnChit(cuePre, cueSerder)

    def sendOwnChit(self, cuePre, cueSerder):
        """
        Send chit of event indicated by cuePre and cueSerder
        """
        # send own chit of event
        # create seal of own last est event
        kever = self.hab.kevers[self.hab.pre]
        seal = eventing.SealEvent(pre=self.hab.pre,
                                  dig=kever.lastEst.dig)

        cueKed = cueSerder.ked
        # create validator receipt
        reserder = eventing.chit(pre=cuePre,
                                 sn=int(cueKed["sn"], 16),
                                 dig=cueSerder.dig,
                                 seal=seal)
        # sign cueSerder event not receipt
        counter = coring.SigCounter(count=1)
        # use signer that matcher current verfer  # not multisig
        verfer = kever.verfers[0]
        siger = None
        for signer in self.hab.signers:
            if signer.verfer.qb64 == verfer.qb64:
                siger = signer.sign(ser=cueSerder.raw, index=0)  # return Siger if index
                break
        if siger:
            # process own chit so have copy in own log
            msg = bytearray(reserder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)
            self.kevery.processOne(ims=bytearray(msg), framed=True)  # make copy

            # send to remote
            self.incomer.tx(bytes(msg))  #  make copy because tx uses deque
            print("{} sent chit:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]


    def sendOwnInception(self):
        """
        Utility to send own inception on client
        """
        # send own inception
        esn = 0
        counter = coring.SigCounter()  # default is count = 1
        # sign serialization, returns Siger if index provided
        siger = self.hab.signers[esn].sign(self.hab.inception.raw, index=0)
        #  create serialized message
        msg = bytearray(self.hab.inception.raw)
        msg.extend(counter.qb64b)
        msg.extend(siger.qb64b)

        # check valid by creating own Kever using own Kevery
        #self.kevery.processOne(ims=bytearray(msg))  # copy of msg
        #kever = self.kevery.kevers[self.hab.pre]
        #assert kever.prefixer.qb64 == self.hab.pre

        # send to connected remote
        self.incomer.tx(bytes(msg))  # make copy for now fix later
        print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
        del msg[:]  #  clear msg




class BobDirector(Director):
    """
    Direct Mode KERI Director (Contextor, Doer) with TCP Client and Kevery
    Generator logic is to iterate through initiation of events for demo

    Inherited Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP client instance. Assumes operated by another doer.
        .kevery is Kevery instance


    Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            # recur context
            tyme = (yield (self.tock))  # yields tock then waits for next send

            while (not self.client.connected):
                # print("{} waiting for connection to remote.\n".format(self.hab.pre))
                tyme = (yield (self.tock))

            print("{}:\n connected to {}.\n\n".format(self.hab.pre, self.client.ha))

            # Inception Event 0
            sn =  0
            esn = 0
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization, returns Siger if index provided
            siger = self.hab.signers[esn].sign(self.hab.inception.raw, index=0)
            #  create serialized message
            msg = bytearray(self.hab.inception.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # check valid by creating own Kever using own Kevery
            self.kevery.processOne(ims=bytearray(msg))  # copy of msg
            kever = self.kevery.kevers[self.hab.pre]
            assert kever.prefixer.qb64 == self.hab.pre

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))

            # Rotation Event 1
            sn += 1
            esn += 1

            kever = self.hab.kevers[self.hab.pre]  # have to do here after own inception

            serder = eventing.rotate(pre=kever.prefixer.qb64,
                        keys=[self.hab.signers[esn].verfer.qb64],
                        dig=kever.diger.qb64,
                        nxt=coring.Nexter(keys=[self.hab.signers[esn+1].verfer.qb64]).qb64,
                        sn=sn)
            # create sig counter
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization
            siger = self.hab.signers[esn].sign(serder.raw, index=0)  # returns siger

            #  create serialized message
            msg = bytearray(serder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # update ownkey event verifier state
            self.kevery.processOne(ims=bytearray(msg))  # make copy

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))

            # Next Event 2 Interaction
            sn += 1  #  do not increment esn

            serder = eventing.interact(pre=kever.prefixer.qb64,
                                       dig=kever.diger.qb64,
                                       sn=sn)

            # create sig counter
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization
            siger = self.hab.signers[esn].sign(serder.raw, index=0)  # returns siger

            # create msg
            msg = bytearray(serder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # update ownkey event verifier state
            self.kevery.processOne(ims=bytearray(msg))  # make copy

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))


        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration



class SamDirector(Director):
    """
    Direct Mode KERI Director (Contextor, Doer) with TCP Client and Kevery
    Generator logic is to iterate through initiation of events for demo

    Inherited Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP client instance. Assumes operated by another doer.
        .kevery is Kevery instance


    Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            # recur context
            tyme = (yield (self.tock))  # yields tock then waits for next send

            while (not self.client.connected):
                # print("{} waiting for connection to remote.\n".format(self.hab.pre))
                tyme = (yield (self.tock))

            print("{}:\n connected to {}.\n\n".format(self.hab.pre, self.client.ha))

            # Inception Event 0
            sn =  0
            esn = 0
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization, returns Siger if index provided
            siger = self.hab.signers[esn].sign(self.hab.inception.raw, index=0)
            #  create serialized message
            msg = bytearray(self.hab.inception.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # check valid by creating own Kever using own Kevery
            self.kevery.processOne(ims=bytearray(msg))  # copy of msg
            kever = self.kevery.kevers[self.hab.pre]
            assert kever.prefixer.qb64 == self.hab.pre

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))


            # Next Event 1 Interaction
            sn += 1  #  do not increment esn

            serder = eventing.interact(pre=kever.prefixer.qb64,
                                       dig=kever.diger.qb64,
                                       sn=sn)

            # create sig counter
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization
            siger = self.hab.signers[esn].sign(serder.raw, index=0)  # returns siger

            # create msg
            msg = bytearray(serder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # update ownkey event verifier state
            self.kevery.processOne(ims=bytearray(msg))  # make copy

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))

            # Rotation Event 2
            sn += 1
            esn += 1

            kever = self.hab.kevers[self.hab.pre]  # have to do here after own inception

            serder = eventing.rotate(pre=kever.prefixer.qb64,
                                             keys=[self.hab.signers[esn].verfer.qb64],
                                dig=kever.diger.qb64,
                                nxt=coring.Nexter(keys=[self.hab.signers[esn+1].verfer.qb64]).qb64,
                                sn=sn)
            # create sig counter
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization
            siger = self.hab.signers[esn].sign(serder.raw, index=0)  # returns siger

            #  create serialized message
            msg = bytearray(serder.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # update ownkey event verifier state
            self.kevery.processOne(ims=bytearray(msg))  # make copy

            # send to connected remote
            self.client.tx(bytes(msg))  # make copy for now fix later
            print("{} sent event:\n{}\n\n".format(self.hab.pre, bytes(msg)))
            del msg[:]  #  clear msg

            tyme = (yield (self.tock))



        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration



class EveDirector(Director):
    """
    Direct Mode KERI Director (Contextor, Doer) with TCP Client and Kevery
    Generator logic is to iterate through initiation of events for demo

    Inherited Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP client instance. Assumes operated by another doer.
        .kevery is Kevery instance


    Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
    """


    def do(self, tymist, tock=0.0, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            # recur context
            tyme = (yield (tock))  # yields tock then waits for next send

            esn = 0
            counter = coring.SigCounter()  # default is count = 1
            # sign serialization, returns Siger if index provided
            siger = self.hab.signers[esn].sign(self.hab.inception.raw, index=0)
            #  create serialized message
            msg = bytearray(self.hab.inception.raw)
            msg.extend(counter.qb64b)
            msg.extend(siger.qb64b)

            # check valid by creating own Kever using own Kevery
            self.kevery.processOne(ims=bytearray(msg))  # copy of msg
            kever = self.kevery.kevers[self.hab.pre]
            assert kever.prefixer.qb64 == self.hab.pre


            tyme = (yield (tock))

            while (not self.client.connected):
                # print("{} waiting for connection to remote.\n".format(self.hab.pre))
                tyme = (yield (self.tock))

            print("{}:\n connected to {}.\n\n".format(self.hab.pre, self.client.ha))
            tyme = (yield (self.tock))



        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration





def runController(doers, limit=0.0):
    """
    run the doers for limit time. 0.0 means no limit.
    """
    # run components
    tock = 0.03125
    doist = doing.Doist(limit=limit, tock=tock, real=True, doers=doers)
    doist.do()


def setupController(secrets,  name="who", remotePort=5621, localPort=5620):
    """
    Setup and return doers list to run controller
    """
    # setup components
    db = dbing.Baser(name=name, temp=True, reopen=False)
    dbDoer = dbing.BaserDoer(baser=db)

    kevers = dict()
    hab = Habitat(secrets=secrets, kevers=kevers, db=db)

    print("Direct Mode demo of {} as {} on TCP port {} to port {}.\n\n"
          "".format(name, hab.pre, localPort, remotePort))

    client = clienting.Client(host='127.0.0.1', port=remotePort)
    clientDoer = doing.ClientDoer(client=client)

    if name == 'bob':
        director = BobDirector(hab=hab, client=client, tock=0.125)
    elif name == "sam":
        director = SamDirector(hab=hab, client=client, tock=0.125)
    else:
        director = EveDirector(hab=hab, client=client, tock=0.125)
    reactor = Reactor(hab=hab, client=client)

    server = serving.Server(host="", port=localPort)
    serverDoer = doing.ServerDoer(server=server)
    directant = Directant(hab=hab, server=server)
    # Reactants created on demand

    return [dbDoer, clientDoer, director, reactor, serverDoer, directant]
