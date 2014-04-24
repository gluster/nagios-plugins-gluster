#!/usr/bin/python
# Copyright (C) 2014 Red Hat Inc
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

import argparse
import json

from glusternagios import utils
from glusternagios import glustercli


def getVolumeStatus(args):
    exitstatus = 0
    message = ""
    try:
        volumes = glustercli.volumeInfo(args.volume)
        if volumes.get(args.volume) is None:
            exitstatus = utils.PluginStatusCode.CRITICAL
            message = "CRITICAL: Volume not found"
            return exitstatus, message
        elif volumes[args.volume]["volumeStatus"] == (glustercli.
                                                      VolumeStatus.ONLINE):
            ret_volumes = {}
            ret_volumes[args.volume] = volumes.get(args.volume)
            ret_volumes[args.volume]['options'] = {}
            exitstatus = utils.PluginStatusCode.OK
            message = ("OK: Volume is up \n%s" % json.dumps(ret_volumes))
        elif volumes[args.volume]["volumeStatus"] == (glustercli.
                                                      VolumeStatus.OFFLINE):
            exitstatus = utils.PluginStatusCode.CRITICAL
            message = "CRITICAL: Volume is stopped"
    except glustercli.GlusterCmdFailedException as e:
        out = ("UNKNOWN: Command execution failed %s" % e.message)
        return utils.PluginStatusCode.UNKNOWN, out

    return exitstatus, message


def getVolumeQuotaStatus(args):
    try:
        status = glustercli.volumeQuotaStatus(args.volume)
    except glustercli.GlusterCmdFailedException as e:
        out = ("QUOTA: Quota status could not be determined %s"
               % '.'.join(e.err))
        return utils.PluginStatusCode.UNKNOWN, out

    if status == glustercli.VolumeQuotaStatus.EXCEEDED:
        return utils.PluginStatusCode.WARNING, "QUOTA: limit exceeded"
    elif status == glustercli.VolumeQuotaStatus.DISABLED:
        return utils.PluginStatusCode.OK, "QUOTA: not enabled or configured"
    else:
        return utils.PluginStatusCode.OK, "QUOTA: OK"


def getVolumeSelfHealStatus(args):
    try:
        volume = glustercli.volumeHealSplitBrainStatus(args.volume)
    except glustercli.GlusterCmdFailedException as e:
        out = ("Self heal status could not be determined - %s"
               % '.'.join(e.err))
        return utils.PluginStatusCode.WARNING, out

    if volume.get(args.volume) is None:
        exitstatus = utils.PluginStatusCode.UNKNOWN
        message = "UNKNOWN: Volume self heal info not found"
    else:
        if (volume[args.volume]['status'] == glustercli.
                VolumeSplitBrainStatus.NOTAPPLICABLE):
            exitstatus = utils.PluginStatusCode.OK
            message = "Volume is not of replicate type"
        elif (volume[args.volume]['status'] == glustercli.
                VolumeSplitBrainStatus.OK):
            exitstatus = utils.PluginStatusCode.OK
            message = "No unsynced entries present"
        elif (volume[args.volume]['status'] == glustercli.
                VolumeSplitBrainStatus.SPLITBRAIN):
            exitstatus = utils.PluginStatusCode.CRITICAL
            message = ("Unsynced entries present %s"
                       % (volume[args.volume]['unsyncedentries']))
    return exitstatus, message


def getVolumeGeoRepStatus(args):
    try:
        volume = glustercli.volumeGeoRepStatus(args.volume)
    except glustercli.GlusterCmdFailedException as e:
        out = ("Geo replication status could not be determined - %s"
               % '.'.join(e.err))
        return utils.PluginStatusCode.WARNING, out

    if volume.get(args.volume) is None:
        exitstatus = utils.PluginStatusCode.UNKNOWN
        message = "UNKNOWN: Volume info not found"
    else:
        if (volume[args.volume]['status'] ==
                glustercli.GeoRepStatus.PARTIAL_FAULTY):
            exitstatus = utils.PluginStatusCode.WARNING
            message = "Partially faulty - %s" % volume[args.volume]['detail']
        elif volume[args.volume]['status'] == glustercli.GeoRepStatus.FAULTY:
            exitstatus = utils.PluginStatusCode.CRITICAL
            message = "Faulty - %s" % volume[args.volume]['detail']
        elif (volume[args.volume]['status'] ==
              glustercli.GeoRepStatus.NOT_STARTED):
            exitstatus = utils.PluginStatusCode.WARNING
            message = "Not Started"
        else:
            exitstatus = utils.PluginStatus.OK
            message = "OK"
    return exitstatus, message


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--volume", action="store",
                        required=True,
                        help="Name of the volume for status")
    parser.add_argument("-t", "--type", action="store",
                        default="info",
                        dest="type",
                        help="Type of status to be shown. Possible values:",
                        choices=["info", "quota", "self-heal", "geo-rep"])
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_input()
    if args.type == "info":
        exitstatus, message = getVolumeStatus(args)
    if args.type == "quota":
        exitstatus, message = getVolumeQuotaStatus(args)
    if args.type == "self-heal":
        exitstatus, message = getVolumeSelfHealStatus(args)
    if args.type == "geo-rep":
        exitstatus, message = getVolumeGeoRepStatus(args)
    print message
    exit(exitstatus)
