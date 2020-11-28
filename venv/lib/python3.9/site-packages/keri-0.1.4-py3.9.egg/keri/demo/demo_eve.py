# -*- encoding: utf-8 -*-
"""
KERI
keri.demo.demoing module

Utilities for demos
"""
import os
import argparse
import logging

from keri import __version__
from keri.base import directing
from keri.help import ogling  # logger support

def runDemo(name="eve", remote=5620, local=5621, expire=0.0):
    """
    Setup and run one demo controller for Eve
    """

    # set of secrets (seeds for private keys)
    secrets = ['AgjD4nRlycmM5cPcAkfOATAp8wVldRsnc9f1tiwctXlw',
                'AKUotEE0eAheKdDJh9QvNmSEmO_bjIav8V_GmctGpuCQ',
                'AK-nVhMMJciMPvmF5VZE_9H-nhrgng9aJWf7_UHPtRNM',
                'AT2cx-P5YUjIw_SLCHQ0pqoBWGk9s4N1brD-4pD_ANbs',
                'Ap5waegfnuP6ezC18w7jQiPyQwYYsp9Yv9rYMlKAYL8k',
                'Aqlc_FWWrxpxCo7R12uIz_Y2pHUH2prHx1kjghPa8jT8',
                'AagumsL8FeGES7tYcnr_5oN6qcwJzZfLKxoniKUpG4qc',
                'ADW3o9m3udwEf0aoOdZLLJdf1aylokP0lwwI_M2J9h0s']

    doers = directing.setupController(secrets=secrets,
                                      name=name,
                                      remotePort=remote,
                                      localPort=local)

    directing.runController(doers=doers, limit=expire)




def parseArgs(version=__version__):
    d = "Runs KERI direct mode demo controller.\n"
    d += "Example:\nkeri_eve -r 5620 -l 5621 --e 10.0\n"
    p = argparse.ArgumentParser(description=d)
    p.add_argument('-V', '--version',
                   action='version',
                   version=version,
                   help="Prints out version of script runner.")
    p.add_argument('-r', '--remote',
                   action='store',
                   default=5620,
                   help="Remote port number the client connects to. Default is 5621.")
    p.add_argument('-l', '--local',
                   action='store',
                   default=5621,
                   help="Local port number the server listens on. Default is 5620.")
    p.add_argument('-e', '--expire',
                   action='store',
                   default=0.0,
                   help="Expire time for demo. 0.0 means not expire. Default is 0.0.")
    p.add_argument('-n', '--name',
                   action='store',
                   default="eve",
                   help="Name of controller. Default is eve. Choices are bob, sam, or eve.")


    args = p.parse_args()

    return args


def main():
    args = parseArgs(version=__version__)

    ogling.ogler.level = logging.DEBUG  # default to debug level

    runDemo(name=args.name,
            remote=args.remote,
            local=args.local,
            expire=args.expire)


if __name__ == "__main__":
    main()

