#!/usr/bin/env python3

"""
This script will make a Jellyfin user account on Jellyfin Server B for each Jellyfin user currently with access to Jellyfin Server A.
Each new user account will have the same username and a randomly-generated alphanumeric password.
"""

import json
import random
import string
import helpers.jellyfin as jf
import helpers.creds as settings

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

jellyfin_src = jf.Jellyfin(url=JF_SRC_URL,
                           api_key=JF_SRC_API_KEY,
                           username=JF_SRC_ADMIN_USERNAME,
                           password=JF_SRC_ADMIN_PASSWORD,
                           default_policy=settings.JELLYFIN_USER_POLICY)

jellyfin_dest = jf.Jellyfin(url=JF_DEST_URL,
                            api_key=JF_DEST_API_KEY,
                            username=JF_DEST_ADMIN_USERNAME,
                            password=JF_DEST_ADMIN_PASSWORD,
                            default_policy=settings.JELLYFIN_USER_POLICY)

user_list = {}


def password(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def add_password(uid):
    pwd = password(length=10)
    if jellyfin_dest.resetPassword(userId=uid):
        if jellyfin_dest.setUserPassword(userId=uid, currentPass="", newPass=pwd):
            return pwd
    return None


def update_policy(uid, policy=None):
    if jellyfin_dest.updatePolicy(userId=uid, policy=policy):
        return True
    return False


def make_jellyfin_user(username, on_server):
    try:
        pwd = None
        jellyfin_user, failure_msg = on_server.makeUser(username=username)
        if jellyfin_user:
            pwd = add_password(uid=jellyfin_user.id)
            if not pwd:
                print("Password update failed. Moving on...")
            if update_policy(uid=jellyfin_user.id, policy=on_server.policy):
                return True, jellyfin_user.id, pwd
            else:
                return False, jellyfin_user.id, pwd
        return False, failure_msg, pwd
    except Exception as e:
        print(f"Error in make_jellyfin_user: {e}")
    return False, None, None


def move_to_jellyfin(username):
    print(f"Adding {username} to Jellyfin...")
    succeeded, uid, pwd = make_jellyfin_user(username=username, on_server=jellyfin_dest)
    if succeeded:
        user_list[username] = [uid, pwd]
        return True, None
    else:
        if uid:
            return False, uid
        return False, None


if __name__ == '__main__':
    print("Beginning user migration...")
    for user in jellyfin_src.getUsers():
        if user.name:
            success, failure_reason = move_to_jellyfin(username=user.name)
            if success:
                print(f"{user.name} added to Jellyfin.")
            else:
                print(f"{user.name} was not added to Jellyfin. Reason: {failure_reason}")
    print("User migration complete.")
    if user_list:
        print("\nUsername ---- Password")
        for k, v in user_list.items():
            print(f"{k}  |  {v[1]}")
