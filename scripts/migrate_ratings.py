#!/usr/bin/env python3

"""
This script will grab each movie or music track on your Plex Media Server with a custom user rating, and add the
rating on the corresponding item on Jellyfin.
"""

import helpers.jellyfin as jf
import helpers.plex as px
import helpers.creds as settings
from progress.bar import Bar

plex = px.Plex(url=settings.PLEX_URL,
               token=settings.PLEX_TOKEN,
               server_name=settings.PLEX_SERVER_NAME)
jellyfin = jf.Jellyfin(url=settings.JELLYFIN_URL,
                       api_key=settings.JELLYFIN_API_KEY,
                       username=settings.JELLYFIN_ADMIN_USERNAME,
                       password=settings.JELLYFIN_ADMIN_PASSWORD,
                       default_policy=settings.JELLYFIN_USER_POLICY)


def moveRatingToJellyfin(title, rating):
    upvote = "true"
    if rating < 6.0:
        upvote = "false"
    search_results = jellyfin.search(keyword=title)
    if search_results:
        jellyfin_item = search_results[0]
        res = jellyfin.updateRating(itemId=jellyfin_item.id, upvote=upvote)
        if res:
            return True
    return False


print("Beginning rating migration...")
for section in plex.get_library_sections():
    # only movies and songs have user ratings
    if section.type in ['movie']:
        all_items = plex.get_all_section_items(section=section)
        bar = Bar(f'Migrating Plex {section.type} ratings to Jellyfin', max=len(all_items))
        success_count = 0
        for movie in all_items:
            if movie.userRating:  # No rating = None
                if moveRatingToJellyfin(title=movie.title, rating=movie.userRating):
                    success_count += 1
            bar.next()
        bar.finish()
        print(f"Updated ratings on Jellyfin for {success_count} {section.type}s.")
    elif section.type in ['artist']:
        all_items = plex.get_all_section_items(section=section)
        success_count = 0
        for artist in all_items:
            all_tracks = artist.tracks()
            bar = Bar(f'Migrating {len(all_tracks)} track ratings from Plex to Jellyfin', max=len(all_tracks))
            for track in all_tracks:
                if track.userRating > 0.0:  # No rating = 0.0
                    if moveRatingToJellyfin(title=track.title, rating=track.userRating):
                        success_count += 1
                bar.next()
            bar.finish()
        print(f"Updated ratings on Jellyfin for {success_count} tracks.")
print("Rating migration complete.")
