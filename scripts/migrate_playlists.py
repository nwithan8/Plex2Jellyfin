#!/usr/bin/env python3

import helpers.jellyfin as jf
import helpers.plex as px

jf.authenticate()
plex = px.server


print("Beginning playlist migration...")
for playlist in plex.playlists():
    #print(playlist.title)
    res = jf.makePlaylist(playlist.title)
    if res.status_code == 200:
        itemList = []
        for item in playlist.items():
            item = jf.search(item.title)[0]
            print(item['Name'])
            itemList.append(item['ItemId'])
        jf.addToPlaylist(str(res.json()['PlaylistId']), itemList)
print("Playlist migration complete.")
