import argparse
import logging
import asyncio

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

server = Server()


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Optional arguments
    parser.add_argument("-i", "--ip", help="IP address of existing node", type=str, default=None)
    parser.add_argument("-p", "--port", help="port number of existing node", type=int, default=None)
    parser.add_argument("-k", "--key", help="key", type=str, default=None)
    parser.add_argument("-v", "--value", help="value", type=str, default=None)

    # Parse arguments
    return parser.parse_args()


async def connect_to_bootstrap_node(args):
    await server.listen(8469)
    bootstrap_node = (args.ip, int(args.port))
    await server.bootstrap([bootstrap_node])
    await server.set(args.key, args.value)
    server.stop()


def create_bootstrap_node():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(8468))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def main():
    args = parse_arguments()

    if args.ip and args.port:
        asyncio.run(connect_to_bootstrap_node(args))
    else:
        create_bootstrap_node()


if __name__ == "__main__":
    main()
