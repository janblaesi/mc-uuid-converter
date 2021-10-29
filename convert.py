#!/usr/bin/env python3
#
# Minecraft Online to offline UUID converter
# Copyright (c) 2021 Jan Blaesi
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import requests
import json
import uuid
import getopt
import sys
import os
from nbt import nbt


"""Current version of the package"""
VERSION = '1.0.0'


class NULL_NAMESPACE:
    """This garbage is needed to replicate the behavior of the UUID.nameUUIDfromBytes function present in Java."""
    bytes = b''


def name_to_online_uuid(name):
    """Return the *online* UUID of a player name"""
    api_reply = requests.get('https://api.mojang.com/users/profiles/minecraft/%s' % name)
    try:
        reply_json = json.loads(api_reply.content.decode('utf-8'))
    except:
        return None

    if 'id' in reply_json:
        return uuid.UUID(reply_json['id'])
    return None

def online_uuid_to_name(uuid):
    """Return the player name of an *online* UUID"""
    api_reply = requests.get('https://api.mojang.com/user/profile/%s' % uuid)
    try:
        reply_json = json.loads(api_reply.content)
    except:
        return None
    
    if 'name' in reply_json:
        return reply_json['name']
    return None

def name_to_offline_uuid(name):
    """Return the *offline* UUID of a player name"""
    return uuid.uuid3(NULL_NAMESPACE, 'OfflinePlayer:%s' % name)

def print_usage():
    """Print the usage of the program to console"""
    print('MC Online to offline UUID converter V%s' % VERSION)
    print('(C) 2021 Jan Blaesi')
    print('')
    print('%s [-h] [-p <path_to_world>]' % sys.argv[0])
    print('')
    print('-p <path_to_world>   Path to the world in which the player data files shall be updated, defaults to ./world')
    print('-h                   Show this help')

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hp:", ["path="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    path = '%s/world' % os.getcwd()
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ('-p', '--path'):
            path = arg
    
    if not path:
        print('No world path specified!')
        sys.exit(1)
    
    if not os.path.isdir('%s/playerdata' % path):
        print('Invalid world path specified!')
        sys.exit(1)

    num_converted = 0
    num_failed = 0
    uuid_cache = {}
    for dir in ['advancements', 'playerdata', 'stats']:
        for file in os.scandir('%s/%s' % (path, dir)):
            if file.is_file() and (file.name.endswith('.dat') or file.name.endswith('.json')):
                try:
                    online_uuid = uuid.UUID(file.name.split('.')[0])
                except:
                    print('Failed to read player data file %s' % file.name)
                    num_failed += 1
                    continue

                if online_uuid in uuid_cache:
                    offline_uuid = uuid_cache[online_uuid]
                else:
                    player_name = online_uuid_to_name(online_uuid)
                    if not player_name:
                        print('Failed to get username for UUID %s' % online_uuid)
                        num_failed += 1
                        continue

                    offline_uuid = name_to_offline_uuid(player_name)
                    if not offline_uuid:
                        print('Failed to get offline UUID from username %s' % player_name)
                        num_failed += 1
                        continue

                    uuid_cache[online_uuid] = offline_uuid

                os.rename(file.path, file.path.replace(str(online_uuid), str(offline_uuid)))
                num_converted += 1

    print('%d files converted successfully, %d failed.' % (num_converted, num_failed))

if __name__ == '__main__':
    main(sys.argv[1:])
