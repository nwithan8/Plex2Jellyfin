from plexapi.server import PlexServer


class Plex:
    def __init__(self, url, token, server_name):
        self.url = url
        self.token = token
        self.server_name = server_name
        self.server = PlexServer(url, token)

    def get_users(self):
        return self.server.myPlexAccount().users()

    def user_has_server_access(self, user):
        for s in user.servers:
            if s.name == self.server_name:
                return True
        return False

    def get_playlists(self):
        return self.server.playlists()

    def get_library_sections(self):
        return self.server.library.sections()

    def get_all_section_items(self, section):
        return section.all()
