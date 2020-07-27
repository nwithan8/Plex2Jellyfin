#!/usr/bin/env python3

"""
This script will make a Jellyfin playlist for each playlist on your Plex Media Server.
Every item on each Plex playlist will be located and added to the new Jellyfin playlist.
"""

import helpers.jellyfin as jf
import helpers.plex as px
import creds as settings
from progress.bar import Bar
import sys
import signal
import time

plex = px.Plex(url=settings.PLEX_URL,
               token=settings.PLEX_TOKEN,
               server_name=settings.PLEX_SERVER_NAME)
jellyfin = jf.Jellyfin(url=settings.JELLYFIN_URL,
                       api_key=settings.JELLYFIN_API_KEY,
                       username=settings.JELLYFIN_ADMIN_USERNAME,
                       password=settings.JELLYFIN_ADMIN_PASSWORD,
                       default_policy=settings.JELLYFIN_USER_POLICY)


def signal_handler(signum, frame):
    print('Canceling...')
    exit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    print("Beginning playlist migration...")
    for plex_playlist in plex.get_playlists():
        # print(playlist.title)
        jellyfin_playlist = jellyfin.makePlaylist(name=plex_playlist.title)
        if jellyfin_playlist:
            print(f'Migrating "{plex_playlist.title}"...')
            itemList = []
            plex_items = plex_playlist.items()
            bar = Bar(f'Matching Plex items on Jellyfin', max=len(plex_items))
            for plex_item in plex_items:
                jellyfin_item = jellyfin.findPlexItemOnJellyfin(plex_item=plex_item)
                if jellyfin_item:
                    itemList.append(jellyfin_item.id)
                bar.next()
            bar.finish()
            print(f"Adding {len(itemList)} matched items to {plex_playlist.title} on Jellyfin...")
            jellyfin.addToPlaylist(playlistId=jellyfin_playlist.id, itemIds=itemList)
            print(f'"{plex_playlist.title}" complete.')
        else:
            print(f'Could not migrate "{plex_playlist.title}"')
    print("Playlist migration complete.")
