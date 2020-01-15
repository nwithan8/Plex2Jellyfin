#!/usr/bin/env python3

import helpers.jellyfin as jf
import helpers.plex as px

jf.authenticate()
plex = px.server


def moveRatingToJellyfin(title, rating):
    upvote = "true"
    if rating < 6:
        upvote = "false"
    item = jf.search(title)[0]
    print(item['Name'])
    res = jf.updateRating(item['ItemId'], upvote)
    print(res.status_code)


print("Beginning rating migration...")
for section in plex.library.sections():
    # only movies and songs have user ratings
    if section.type in ['movie']:
        for movie in section.all():
            if movie.userRating:  # No rating = None
                print(movie.title)
                moveRatingToJellyfin(movie.title, movie.userRating)
    if section.type in ['artist']:
        for artist in section.all():
            for track in artist.tracks():
                if track.userRating != 0.0:  # No rating = 0.0
                    print(track.title)
                    moveRatingToJellyfin(track.title, track.userRating)
print("Rating migration complete.")
