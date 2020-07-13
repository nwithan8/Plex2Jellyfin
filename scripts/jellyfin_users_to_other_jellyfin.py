#!/usr/bin/env python3

"""
This script will make a Jellyfin user account on Jellyfin Server B for each Jellyfin user currently with access to Jellyfin Server A.
Each new user account will have the same username and a randomly-generated alphanumeric password.
"""

import json
import random
import string
import helpers.jellyfin as jf_src
import helpers.jellyfin as jf_dest

# Details for first Jellyfin server (source server)
JF_SRC_URL = ''
JF_SRC_API_KEY = ''
JF_SRC_ADMIN_USERNAME = ''
JF_SRC_ADMIN_PASSWORD = ''

# Details for second Jellyfin server (destination server)
JF_DEST_URL = ''
JF_DEST_API_KEY = ''
JF_DEST_ADMIN_USERNAME = ''
JF_DEST_ADMIN_PASSWORD = ''

user_list = {}


def password(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def add_password(uid):
    p = password(length=10)
    r = jf_dest.resetPassword(uid)
    if str(r.status_code).startswith('2'):
        r = jf_dest.setUserPassword(uid, "", p)
        if str(r.status_code).startswith('2'):
            return p
    return None


def update_policy(uid, policy=None):
    if str(jf_dest.updatePolicy(uid, policy).status_code).startswith('2'):
        return True
    return False


def make_jellyfin_user(username):
    try:
        p = None
        r = jf_dest.makeUser(username)
        if str(r.status_code).startswith('2'):
            r = json.loads(r.text)
            uid = r['Id']
            p = add_password(uid)
            if not p:
                print("Password update failed. Moving on...")
            if update_policy(uid, jf_dest.JELLYFIN_USER_POLICY):
                return True, uid, p
            else:
                return False, uid, p
        return False, r.content.decode("utf-8"), p
    except Exception as e:
        print(e)
        return False, None, None


def move_to_jellyfin(username):
    print("Adding {} to Jellyfin...".format(username))
    succeeded, uid, pwd = make_jellyfin_user(username)
    if succeeded:
        user_list[username] = [uid, pwd]
        return True, None
    else:
        if uid:
            return False, uid
        return False, None


jf_src.JELLYFIN_URL = JF_SRC_URL
jf_src.JELLYFIN_API_KEY = JF_SRC_API_KEY
jf_src.JELLYFIN_ADMIN_USERNAME = JF_SRC_ADMIN_USERNAME
jf_src.JELLYFIN_ADMIN_PASSWORD = JF_SRC_ADMIN_PASSWORD
jf_src.authenticate()
jf_src.JELLYFIN_URL = JF_SRC_URL
jf_src.JELLYFIN_API_KEY = JF_SRC_API_KEY
jf_src.JELLYFIN_ADMIN_USERNAME = JF_SRC_ADMIN_USERNAME
jf_src.JELLYFIN_ADMIN_PASSWORD = JF_SRC_ADMIN_PASSWORD

jf_dest.JELLYFIN_URL = JF_DEST_URL
jf_dest.JELLYFIN_API_KEY = JF_DEST_API_KEY
jf_dest.JELLYFIN_ADMIN_USERNAME = JF_DEST_ADMIN_USERNAME
jf_dest.JELLYFIN_ADMIN_PASSWORD = JF_DEST_ADMIN_PASSWORD
jf_dest.authenticate()
jf_dest.JELLYFIN_URL = JF_DEST_URL
jf_dest.JELLYFIN_API_KEY = JF_DEST_API_KEY
jf_dest.JELLYFIN_ADMIN_USERNAME = JF_DEST_ADMIN_USERNAME
jf_dest.JELLYFIN_ADMIN_PASSWORD = JF_DEST_ADMIN_PASSWORD

print("Beginning user migration...")
print(jf_src.JELLYFIN_URL)
for user in jf_src.getUsers():
    if user.get('name'):
        success, failure_reason = move_to_jellyfin(user['name'])
        if success:
            print("{} added to Jellyfin.".format(user.username))
        else:
            print("{} was not added to Jellyfin. Reason: {}".format(user.username, failure_reason))
        break
print("User migration complete.")
if user_list:
    print("\nUsername ---- Password")
    for k, v in user_list.items():
        print(str(k) + "  |  " + str(v[1]))
