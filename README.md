# Plex2Jellyfin

Scripts to assist migrating from a Plex Media Server to a Jellyfin Media Server

- Migrate users: Creates a new user account on Jellyfin for each Plex user with access to your Plex Media Server
- Migrate ratings: Copies user ratings of media items from Plex over to Jellyfin
- Migrate playlists: Scan Plex playlists to create and populate identical playlists on Jellyfin
- Migrate Jellyfin users to another Jellyfin server: Mirror all Jellyfin users from one server to another server

# Install & Run

1. Ensure `uv` is present on the system (see the [uv docs](https://docs.astral.sh/uv/getting-started/installation/))
2. Clone this repo with `git clone https://github.com/nwithan8/Plex2Jellyfin.git`.
3. Enter the `Plex2Jellyfin` directory
4. Enter the `scripts` folder, `cd scripts`.
5. Copy `creds.py.blank` as `creds.py`, `cp creds.py.blank creds.py`, and complete the information inside.
   - Getting the Plex token: [https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
6. Run a script with `uv run scripts/[SCRIPT NAME]`, e.g. `uv run scripts/migrate_playlists.py`. Dependencies and virtual environments will be handled for you.

**Requires Python 3.6+**
