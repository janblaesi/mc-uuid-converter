#!/usr/bin/env python3

import requests
import json
import uuid
import getopt
import sys
import os


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

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hp:", ["path="])
    except getopt.GetoptError:
        print('%s -p <path_to_world>' % sys.argv[0])
        sys.exit(2)

    path = None
    for opt, arg in opts:
        if opt == '-h':
            print('%s -p <path_to_world>' % sys.argv[0])
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
    for file in os.scandir('%s/playerdata' % path):
        if file.is_file() and file.name.endswith('.dat'):
            try:
                online_uuid = uuid.UUID(file.name.split('.')[0])
            except:
                print('Failed to read player data file %s' % file.name)
                num_failed += 1
                continue

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

            print('%s -> %s -> %s' % (online_uuid, player_name, offline_uuid))
            os.rename(file.path, file.path.replace(file.name, '%s.dat' % offline_uuid))
            num_converted += 1
    
    print('%d player data files converted successfully, %d failed.' % (num_converted, num_failed))

if __name__ == '__main__':
    main(sys.argv[1:])
