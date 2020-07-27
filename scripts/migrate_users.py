#!/usr/bin/env python3

"""
This script will make a Jellyfin user account for each Plex user currently with access to your Plex Media Server (
Sharing Users) Each new user account will have the same Plex name as their Jellyfin username,
and a randomly-generated alphanumeric password.
"""

import json
import random
import string
import helpers.jellyfin as jf
import helpers.plex as px
import creds as settings

plex = px.Plex(url=settings.PLEX_URL,
               token=settings.PLEX_TOKEN,
               server_name=settings.PLEX_SERVER_NAME)
jellyfin = jf.Jellyfin(url=settings.JELLYFIN_URL,
                       api_key=settings.JELLYFIN_API_KEY,
                       username=settings.JELLYFIN_ADMIN_USERNAME,
                       password=settings.JELLYFIN_ADMIN_PASSWORD,
                       default_policy=settings.JELLYFIN_USER_POLICY)

user_list = {}


def password(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def add_password(uid):
    pwd = password(length=10)
    if jellyfin.resetPassword(userId=uid):
        if jellyfin.setUserPassword(userId=uid, currentPass="", newPass=pwd):
            return pwd
    return None


def update_policy(uid, policy=None):
    if jellyfin.updatePolicy(userId=uid, policy=policy):
        return True
    return False


def make_jellyfin_user(username):
    try:
        pwd = None
        jellyfin_user, failure_msg = jellyfin.makeUser(username=username)
        if jellyfin_user:
            pwd = add_password(uid=jellyfin_user.id)
            if not pwd:
                print("Password update failed. Moving on...")
            if update_policy(uid=jellyfin_user.id, policy=jellyfin.policy):
                return True, jellyfin_user.id, pwd
            else:
                return False, jellyfin_user.id, pwd
        return False, failure_msg, pwd
    except Exception as e:
        print(f"Error in make_jellyfin_user: {e}")
    return False, None, None


def convert_plex_to_jellyfin(username):
    print(f"Adding {username} to Jellyfin...")
    succeeded, uid, pwd = make_jellyfin_user(username=username)
    if succeeded:
        user_list[username] = [uid, pwd]
        return True, None
    else:
        if uid:
            return False, uid
    return False, None


if __name__ == '__main__':
    print("Beginning user migration...")
    for plex_user in plex.get_users():
        if plex.user_has_server_access(user=plex_user):
            success, failure_reason = convert_plex_to_jellyfin(username=plex_user.username)
            if success:
                print(f"{plex_user.username} added to Jellyfin.")
            else:
                print(f"{plex_user.username} was not added to Jellyfin. Reason: {failure_reason}")
            break
    print("User migration complete.")
    if user_list:
        print("\nUsername ---- Password")
        for k, v in user_list.items():
            print(f"{k}  |  {v[1]}")
