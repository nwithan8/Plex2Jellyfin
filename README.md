# Plex2Jellyfin
Scripts to assist migrating from a Plex Media Server to a Jellyfin Media Server

- Migrate users: Creates a new user account on Jellyfin for each Plex user with access to your Plex Media Server
- Migrate ratings: Copies user ratings of media items from Plex over to Jellyfin
- Migrate playlists: Scan Plex playlists to create and populate identical playlists on Jellyfin
- Migrate Jellyfin users to another Jellyfin server: Mirror all Jellyfin users from one server to another server

# Install & Run
1. Clone this repo with ``git clone https://github.com/nwithan8/Plex2Jellyfin.git``.
2. Enter the ``Plex2Jellyfin`` directory.
3. Install dependencies with ``pip install -r requirements.txt``
4. Enter the ``scripts`` folder.
5. Copy ``creds.py.blank`` as ``creds.py`` and complete the information inside.
6. Run a script with ``python [SCRIPT NAME]``.

**Requires Python 3.6+**
