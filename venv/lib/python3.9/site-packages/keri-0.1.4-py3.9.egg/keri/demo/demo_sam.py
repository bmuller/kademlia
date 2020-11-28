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

def runDemo(name="sam", remote=5621, local=5620, expire=0.0):
    """
    Setup and run one demo controller for sam, like bob only better
    """

    secrets = [
                'ArwXoACJgOleVZ2PY7kXn7rA0II0mHYDhc6WrBH8fDAc',
                'A6zz7M08-HQSFq92sJ8KJOT2cZ47x7pXFQLPB0pckB3Q',
                'AcwFTk-wgk3ZT2buPRIbK-zxgPx-TKbaegQvPEivN90Y',
                'Alntkt3u6dDgiQxTATr01dy8M72uuaZEf9eTdM-70Gk8',
                'A1-QxDkso9-MR1A8rZz_Naw6fgaAtayda8hrbkRVVu1E',
                'AKuYMe09COczwf2nIoD5AE119n7GLFOVFlNLxZcKuswc',
                'AxFfJTcSuEE11FINfXMqWttkZGnUZ8KaREhrnyAXTsjw',
                'ALq-w1UKkdrppwZzGTtz4PWYEeWm0-sDHzOv5sq96xJY'
                ]

    doers = directing.setupController(secrets=secrets,
                                      name=name,
                                      remotePort=remote,
                                      localPort=local)

    directing.runController(doers=doers, limit=expire)



def parseArgs(version=__version__):
    d = "Runs KERI direct mode demo controller.\n"
    d += "Example:\nkeri_bob -r 5621 -l 5620 --e 10.0'\n"
    p = argparse.ArgumentParser(description=d)
    p.add_argument('-V', '--version',
                   action='version',
                   version=version,
                   help="Prints out version of script runner.")
    p.add_argument('-r', '--remote',
                   action='store',
                   default=5621,
                   help="Remote port number the client connects to. Default is 5621.")
    p.add_argument('-l', '--local',
                   action='store',
                   default=5620,
                   help="Local port number the server listens on. Default is 5620.")
    p.add_argument('-e', '--expire',
                   action='store',
                   default=0.0,
                   help="Expire time for demo. 0.0 means not expire. Default is 0.0.")
    p.add_argument('-n', '--name',
                   action='store',
                   default="sam",
                   help="Name of controller. Default is sam. Choices are bob, sam, or eve.")


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

