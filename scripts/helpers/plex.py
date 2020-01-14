import helpers.creds as creds
import requests
import json
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount

PLEX_URL = creds.PLEX_URL
PLEX_TOKEN = creds.PLEX_TOKEN
PLEX_SERVER_NAME = creds.PLEX_SERVER_NAME

server = PlexServer(PLEX_URL, PLEX_TOKEN)
