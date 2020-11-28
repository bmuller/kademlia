# -*- encoding: utf-8 -*-
"""
hio.core.coring Module
"""

import subprocess
import socket

import netifaces

from ..hioing import ValidationError


def normalizeHost(host):
    """
    Returns ip address host string in normalized dotted form or empty string
    converts host parameter which may be the dns name or ip address
    Prefers ipv4 addresses over ipv6 in that it will only return the ipv6
    address if no ipv4 address equivalent is available
    """
    if host == "":
        host = "0.0.0.0"

    try:  # try ipv4
        info =  socket.getaddrinfo(host,
                                   None,
                                   socket.AF_INET,
                                   socket.SOCK_DGRAM,
                                   socket.IPPROTO_IP, 0)
    except socket.gaierror as ex: # try ipv6
        if host in ("", "0.0.0.0"):
            host = "::"

        info =  socket.getaddrinfo(host,
                                    None,
                                    socket.AF_INET6,
                                    socket.SOCK_DGRAM,
                                    socket.IPPROTO_IP, 0)
    if not info:
        raise ValidationError("Cannot resolve address for host '{0}'".format(host))

    host = info[0][4][0]
    return host


def getDefaultHost():
    """
    Returns host ip address of default interface using netifaces
    """
    iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
    info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
    host = info['addr']
    return host


def getDefaultBroadcast():
    """
    Returns broadcast ip address of default interface using netifaces

    """
    iface =  netifaces.gateways()['default'][netifaces.AF_INET][1]
    info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
    bcast = info['broadcast']
    return bcast


def arpCreate(ether, host, interface="en0", temp=True):
    """
    Create arp entry for ethernet mac address ether at ip address host on interface
    If temp is false then the entry is permanent otherwise its temporary

    Assumes added /etc/sudoers entry to run arp with no password for user's group
    $ sudo visudo

    ## Group to run arp as root with no password
    Cmnd_Alias  ARP = /usr/sbin/arp
    %arp_group ALL=(ALL) NOPASSWD: ARP

    """
    temp = "temp" if temp else ""
    console.terse("{0}: Creating {1} arp entry for {2} at {3} on {4}\n".format(
                                        datetime.datetime.utcnow().isoformat(),
                                        temp,
                                        ether,
                                        host,
                                        interface))
    console.flush()

    # sudo arp -s 10.0.2.49 70:b3:d5:0:e0:30 ifscope en3 temp
    try:
        process = subprocess.run(["sudo",
                                  "/usr/sbin/arp",
                                  "-s",
                                  host,
                                  ether,
                                  "ifscope",
                                  interface,
                                  temp],
                                 check=True)
    except subprocess.SubprocessError as ex:
        console.terse("{0}: Failed Creation of {1} arp entry for {2} at {3} on {4}\n".format(
                                                datetime.datetime.utcnow().isoformat(),
                                                temp,
                                                ether,
                                                host,
                                                interface))
    console.flush()


def arpDelete(host, interface="en0"):
    """
    Delete arp entry for ip address host on interface

    Assumes added /etc/sudoers entry to run arp with no password for user's group
    $ sudo visudo

    ## Group to run arp as root with no password
    Cmnd_Alias  ARP = /usr/sbin/arp
    %arp_group ALL=(ALL) NOPASSWD: ARP

    """

    console.terse("{0}: Deleting arp entry at {1} on {2}\n".format(
                                        datetime.datetime.utcnow().isoformat(),
                                        host,
                                        interface))
    console.flush()

    # sudo arp -d 10.0.2.49 ifscope en3
    try:
        process = subprocess.run(["sudo",
                                  "/usr/sbin/arp",
                                  "-d",
                                  host,
                                  "ifscope",
                                  interface],
                                 check=True)
    except subprocess.SubprocessError as ex:
        console.terse("{0}: Failed Deletion of arp entry at {1} on {2}\n".format(
                                                datetime.datetime.utcnow().isoformat(),
                                                host,
                                                interface))
    console.flush()


