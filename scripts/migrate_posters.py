#!/usr/bin/python3

"""This script will grab each movie, show and/or artist on your Plex Media Server, and copy its poster and backdrop
to the same item on your Jellyfin server.
NOTES:
    - Jellyfin will have to have completed an initial scan of your library already (IDs must have been created by
    Jellyfin for each media item)
    - This script will need to be run on the same machine where your files are stored, and both Jellyfin
    and Plex must be running on the same machine.
    - You must specify "path translations" below. This will translate a Plex- or Jellyfin-specific path into a system
    path (helpful if you are running Plex and Jellyfin as Docker containers). If there is no translation needed, simply
    make the app and system paths the same.
    - You can indicate only specific library types (movies, shows, music) to migrate. Use the -h flag to see details.
    - A Plex item's Jellyfin counterpart is found by searching title and year. Warning, this may produce false results.
-
"""
import hashlib
import os
import shutil
import argparse

import helpers.jellyfin as jf
import helpers.plex as px
import creds as settings

# EDIT THE PATH TRANSLATIONS BELOW

# { "path according to app": "real path on your system" }
path_translations = {
    'plex': {
        'App Data': {
            '/config': "/mnt/user/appdata/PlexMediaServer"
        },
        'Media': {
            '/data': "/mnt/user/Plex_Media"
        }
    },
    'jellyfin': {
        'App Data': {
            '/config': '/mnt/user/appdata/jellyfin'
        },
        'Media': {
            '/movies': "/mnt/user/Plex_Media/Movies",
            '/tv': "/mnt/user/Plex_Media/TV Shows",
            '/music': "/mnt/user/Plex_Media/Music",
            '/4k': "/mnt/user/Plex_Media/4K"
        }
    }
}


# DO NOT EDIT BELOW THIS LINE

plex = px.Plex(url=settings.PLEX_URL,
               token=settings.PLEX_TOKEN,
               server_name=settings.PLEX_SERVER_NAME)
jellyfin = jf.Jellyfin(url=settings.JELLYFIN_URL,
                       api_key=settings.JELLYFIN_API_KEY,
                       username=settings.JELLYFIN_ADMIN_USERNAME,
                       password=settings.JELLYFIN_ADMIN_PASSWORD,
                       default_policy=settings.JELLYFIN_USER_POLICY)
# { Media Type: {Plex, Jellyfin}}
metadata_translations = {
    'movie': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/Movies',
        'Jellyfin': '/data/metadata/library'
    },
    'episode': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/TV\ Shows',
        'Jellyfin': '/data/metadata/library'
    },
    'show': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/TV\ Shows',
        'Jellyfin': '/data/metadata/library'
    },
    'season': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/TV\ Shows',
        'Jellyfin': '/data/metadata/library'
    },
    'artist': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/Artists',
        'Jellyfin': '/data/metadata/library'
    },
    'album': {
        'Plex': r'/Library/Application Support/Plex Media Server/Metadata/Albums',
        'Jellyfin': '/data/metadata/library'
    }
}


def sha1(text):
    return hashlib.sha1(text.encode()).hexdigest()


def local_to_global_path(local_path, server_type, folder_type):
    for local, system in path_translations[server_type][folder_type].items():
        if local in local_path:
            return local_path.replace(local, system)
    return local_path


def global_to_local_path(global_path, server_type, folder_type):
    for local, system in path_translations[server_type][folder_type].items():
        if system in global_path:
            return global_path.replace(system, local)
    return global_path


def get_plex_metadata_folder(plex_item, item_type):
    guid = plex_item.guid
    metadata_id = sha1(guid)
    return f"{list(path_translations['plex']['App Data'].keys())[0]}{metadata_translations[item_type]['Plex']}/{metadata_id[0]}/{metadata_id[1:]}.bundle"


def get_jellyfin_metadata_folder(jellyfin_item, item_type):
    jellyfin_id = jellyfin_item.id
    return f"{list(path_translations['jellyfin']['App Data'].keys())[0]}{metadata_translations[item_type]['Jellyfin']}/{jellyfin_id[:2]}/{jellyfin_id}"


def get_plex_image_folder(folder, image_type):
    if image_type == 'poster':
        return f"{folder}/posters"
    elif image_type == 'backdrop':
        return f"{folder}/art"


def get_plex_item_title(plex_item, item_type):
    title = ""
    if item_type == 'movie':
        title = f"{plex_item.title} ({plex_item.year})"
    elif item_type == 'show':
        season_one = plex_item.seasons()[0]
        title = f"{season_one.parentTitle}"
    if item_type == 'season':
        title = f"{plex_item.parentTitle} - Season {plex_item.index}"
    elif item_type == 'episode':
        title = f"{plex_item.grandparentTitle} - Season {plex_item.parentIndex} - Episode {plex_item.index} - {plex_item.title} ({plex_item.year})"
    elif item_type == 'artist':
        title = f"{plex_item.title}"
    elif item_type == 'album':
        title = f"{plex_item.parentTitle} - {plex_item.title} ({plex_item.year})"
    elif item_type == 'track':
        title = f"{plex_item.grandparentTitle} - {plex_item.parentTitle} - {plex_item.title} ({plex_item.year})"
    return title


def get_plex_file(plex_item, item_type, file_type):
    try:
        folder = f"{get_plex_metadata_folder(plex_item=plex_item, item_type=item_type)}/Contents/_stored"
        folder = get_plex_image_folder(folder=folder, image_type=file_type)
        folder = local_to_global_path(local_path=folder, server_type='plex', folder_type='App Data')
        picture_file = os.listdir(folder)[0]
        return picture_file
    except Exception as e:
        print(f"{e}")
    return None


def get_jellyfin_image_file(folder, image_type):
    if image_type == 'poster':
        return f"{folder}/poster.jpg"
    elif image_type == 'backdrop':
        return f"{folder}/backdrop.jpg"


def get_jellyfin_file(jellyfin_item, image_type, item_type):
    try:
        folder = get_jellyfin_metadata_folder(jellyfin_item=jellyfin_item, item_type=item_type)
        file = get_jellyfin_image_file(folder=folder, image_type=image_type)
        file = local_to_global_path(local_path=file, server_type='jellyfin', folder_type='App Data')
        return file
    except Exception as e:
        print(f"{e}")
    return None


def file_exists(file):
    return os.path.exists(file)


def copy_file(src_file, dest_file):
    try:
        if not src_file or not file_exists(src_file):
            return False
        shutil.copy(src=src_file, dst=dest_file)
        return True
    except Exception as e:
        print(f"{e}")
    return False


def move_images_to_jellyfin(plex_item, plex_item_type):
    title = get_plex_item_title(plex_item=plex_item, item_type=plex_item_type)
    jellyfin_item = jellyfin.findPlexItemOnJellyfin(plex_item=plex_item, title=title)
    if jellyfin_item:
        print(f"Plex: {title} --> Jellyfin: {jellyfin_item.name}")
        plex_poster = get_plex_file(plex_item=plex_item, item_type=plex_item_type, file_type='poster')
        plex_backdrop = get_plex_file(plex_item=plex_item, item_type=plex_item_type, file_type='backdrop')
        jellyfin_poster = get_jellyfin_file(jellyfin_item=jellyfin_item, image_type='poster', item_type=plex_item_type)
        jellyfin_backdrop = get_jellyfin_file(jellyfin_item=jellyfin_item, image_type='backdrop',
                                              item_type=plex_item_type)
        if not plex_poster and not plex_backdrop:
            print(f"Neither poster and backdrop exists for this item.")
            return False
        success = True
        if not copy_file(plex_poster, jellyfin_poster):
            success = False
            print(f"Couldn't migrate poster.")
        if not copy_file(plex_backdrop, jellyfin_backdrop):
            success = False
            print(f"Couldn't migrate backdrop.")
        return success
    else:
        print(f"Could not locate {title} on Jellyfin to migrate metadata.")
    return False


def migration_success_message(success_count, item_count, section_type):
    print(f"Successfully migrated metadata for {success_count} of {item_count} {section_type}s")


parser = argparse.ArgumentParser()
parser.add_argument('--libraries', '-l', choices=['movies', 'shows', 'music'], nargs='+', required=False,
                    help="What types of libraries to include in the migration (movies, shows, music)")
args = parser.parse_args()

if not args.libraries:
    args.libraries = ['movies', 'shows', 'music']

for section in plex.get_library_sections():
    if section.type in ['movie'] and 'movies' in args.libraries:
        movie_count = 0
        all_movies = plex.get_all_section_items(section=section)
        for movie in all_movies:
            if move_images_to_jellyfin(plex_item=movie, plex_item_type='movie'):
                movie_count += 1
        migration_success_message(success_count=movie_count, item_count=len(all_movies), section_type='movie')
    if section.type in ['show'] and 'shows' in args.libraries:
        all_shows = plex.get_all_section_items(section=section)
        show_count = 0
        for show in all_shows:
            if move_images_to_jellyfin(plex_item=show, plex_item_type='show'):
                show_count += 1
            all_seasons = show.seasons()
            season_count = 0
            for season in all_seasons:
                if move_images_to_jellyfin(plex_item=season, plex_item_type='season'):
                    season_count += 1
                all_episodes = season.episodes()
                episode_count = 0
                for episode in all_episodes:
                    if move_images_to_jellyfin(plex_item=episode, plex_item_type='episode'):
                        episode_count += 1
                migration_success_message(success_count=episode_count, item_count=len(all_episodes),
                                          section_type='episode')
            migration_success_message(success_count=season_count, item_count=len(all_seasons), section_type='season')
        migration_success_message(success_count=show_count, item_count=len(all_shows), section_type='show')
    if section.type in ['artist'] and 'music' in args.libraries:
        all_artists = plex.get_all_section_items(section=section)
        artist_count = 0
        for artist in all_artists:
            if move_images_to_jellyfin(plex_item=artist, plex_item_type='artist'):
                artist_count += 1
            all_albums = artist.albums()
            album_count = 0
            for album in all_albums:
                if move_images_to_jellyfin(plex_item=album, plex_item_type='album'):
                    album_count += 1
            migration_success_message(success_count=album_count, item_count=len(all_albums), section_type='album')
        migration_success_message(success_count=artist_count, item_count=len(all_artists), section_type='artist')
