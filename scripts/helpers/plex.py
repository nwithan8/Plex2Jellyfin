from plexapi.server import PlexServer


class Plex:
    def __init__(self, url, token, server_name, server=None):
        self.url = url
        self.token = token
        self.server_name = server_name
        self.server = server or PlexServer(url, token)

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

    def as_user(self, user:str):
        """Returns a new instance logged in as the target user

        Args:
            user (str): username of the user to log in as
        """

        return Plex(self.url, self.token, self.server_name, server=self.server.switchUser(user))
