#!/usr/bin/env python3

"""
This script will make an M3u playlist for each playlist for each user on your Plex Media Server.
"""
from pathlib import Path

import helpers.plex as px
from plexapi.exceptions import Unauthorized
import creds as settings
from progress.bar import Bar
import sys
import signal
import time

plex = px.Plex(url=settings.PLEX_URL,
               token=settings.PLEX_TOKEN,
               server_name=settings.PLEX_SERVER_NAME)

def signal_handler(signum, frame):
    print('Canceling...')
    exit()


def playlists_for(user:str = None):
    if user is not None:
        try:
            plex_as_user = plex.as_user(user)
        except Unauthorized:
            return None
        return plex_as_user.get_playlists()
    return plex.get_playlists()
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)


    print("Plex users:")

    print([u.username for u in plex.get_users()])

    DRYRUN = False

    # print(jellyfin.getPlaylists())
    users = plex.get_users()

    BASE_PATH="./out"

    for u in users:
        if u.username == "":
            continue
        print()
        print(f"Beginning playlist migration for {u.username}...")
        playlists = playlists_for(u.username)
        if playlists is None:
            continue

        for plex_playlist in playlists:
            filename=f"{u.username}_{plex_playlist.title}.m3u"
            output = []
            print(plex_playlist.title)
            output.append("#EXTM3U" + "\n")
            output.append("#PLAYLIST:"+ plex_playlist.title + "\n")
            plex_items = plex_playlist.items()
            for plex_item in plex_items:
                output.append(f"#EXTINF:{int((plex_item.duration or 0)/1000)},{plex_item.title}" + "\n")
                output.append(plex_item.locations[0] + "\n")
            if not Path(BASE_PATH).exists():
                Path(BASE_PATH).mkdir()
            with Path(BASE_PATH).joinpath(filename).open("w", encoding="utf-8") as o:
                o.writelines(output)
    print("Playlist export complete.")
