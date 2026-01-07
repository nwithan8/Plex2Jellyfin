import requests
import socket
import json
from urllib.parse import urlencode
import os
import signal
import sys
import time

token_file = '.jellyfin_token'


def signal_handler(signum, frame):
    print('Canceling...')
    exit()


def _save_token_id(file, creds):
    with open(file, 'w+') as f:
        for line in creds:
            f.write(f"{line}\n")


class JellyfinItem:
    def __init__(self, data):
        self.id = data['ItemId']
        self.name = data['Name']


class JellyfinPlaylist:
    def __init__(self, data):
        self.id = data['Id']


class JellyfinUser:
    def __init__(self, data):
        self.id = data['Id']
        self.name = data['Name']


class Jellyfin:
    def __init__(self, url, api_key, username, password, default_policy, default_config):
        self.url = url
        self.key = api_key
        self.username = username
        self.password = password
        self.user_id = None
        self.policy = default_policy
        self.config = default_config
        self.token_header = None
        self.authenticate(force_new_auth=False)
        signal.signal(signal.SIGINT, signal.default_int_handler)

    def authenticate(self, force_new_auth=False):
        if force_new_auth or not self._load_token_id(token_file):
            print("Authenticating with Jellfin...")
            xEmbyAuth = {
                'X-Emby-Authorization': 'Emby UserId="{UserId}", Client="{Client}", Device="{Device}", '
                                        'DeviceId="{DeviceId}", Version="{Version}", Token="""'.format(
                    UserId="",  # not required, if it was we would have to first request the UserId from the username
                    Client='account-automation',
                    Device=socket.gethostname(),
                    DeviceId=hash(socket.gethostname()),
                    Version=1,
                    Token=""  # not required
                )}
            data = {'Username': self.username, 'Password': self.password,
                    'Pw': self.password}
            try:
                res = self._post_request_with_token(hdr=xEmbyAuth, cmd='/Users/AuthenticateByName', data=data).json()
                self.token_header = {'X-Emby-Token': '{}'.format(res['AccessToken'])}
                self.user_id = res['User']['Id']
                _save_token_id(file=token_file, creds=[res['AccessToken'], res['User']['Id']])
            except Exception as e:
                print('Could not log into Jellyfin.\n{}'.format(e))

    def _load_token_id(self, file):
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = f.readlines()
                self.token_header = {'X-Emby-Token': f'{lines[0].rstrip()}'}
                self.user_id = lines[1].rstrip()
            return True
        return False

    def _get_request(self, cmd, params=None, retried=False):
        try:
            res = requests.get(f'{self.url}{cmd}?api_key={self.key}{("&" + params if params else "")}')
            if res:
                return res.json()
            return {}
        except:
            if retried:
                return {}
            self.authenticate(force_new_auth=True)
        return self._get_request(cmd=cmd, params=params, retried=True)

    def _get_request_with_token(self, hdr, cmd, data=None, retried=False):
        try:
            hdr = {'accept': 'application/json', **hdr}
            res = requests.get(f'{self.url}{cmd}', headers=hdr, data=(json.dumps(data) if data else None))
            if res:
                return res.json()
            return {}
        except:
            if retried:
                return {}
            self.authenticate(force_new_auth=True)
        return self._get_request_with_token(hdr=hdr, cmd=cmd, data=data, retried=True)

    def _post_request(self, cmd, params=None, payload=None, retried=False):
        try:
            res = requests.post(
                f'{self.url}{cmd}?api_key={self.key}{("&" + params if params is not None else "")}',
                json=payload,
                headers={'accept': 'application/json', 'Content-Type': 'application/json'}
            )

            if res:
                return res
            return None
        except:
            if retried:
                return None
            self.authenticate(force_new_auth=True)
        return self._post_request(cmd=cmd, params=params, payload=payload, retried=True)

    def _post_request_json(self, cmd, payload=None, retried=False):
        try:
            res = requests.post(
                f'{self.url}{cmd}?api_key={self.key}',
                json=payload,
                headers={'accept': 'application/json', 'Content-Type': 'application/json'}
            )

            if res:
                return res
            return None
        except:
            if retried:
                return None
            self.authenticate(force_new_auth=True)
        return self._post_request_json(cmd=cmd, payload=payload, retried=True)

    def _post_request_with_token(self, hdr, cmd, data=None, retried=False):
        try:
            hdr = {'accept': 'application/json', 'Content-Type': 'application/json', **hdr}
            res = requests.post(f'{self.url}{cmd}', headers=hdr, json=data)
            if res.status_code == 401 and not retried:
                self.authenticate(force_new_auth=True)
                return self._post_request_with_token(hdr=self.token_header, cmd=cmd, data=data, retried=True)
            return res

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None

    def _delete_request(self, cmd, params=None, retried=False):
        try:
            res = requests.delete(
                f'{self.url}{cmd}?api_key={self.key}{("&" + params if params is not None else "")}')
            if res:
                return res.json()
            return {}
        except:
            if retried:
                return {}
            self.authenticate(force_new_auth=True)
        return self._delete_request(cmd=cmd, params=params, retried=True)

    def makeUser(self, username):
        cmd = '/Users/New'
        data = {
            'Name': str(username)
        }
        res = self._post_request(cmd=cmd, params=None, payload=data)
        if res:
            return JellyfinUser(data=res.json()), None
        return None, res.content.decode("utf-8")

    def deleteUser(self, userId):
        cmd = f'/Users/{userId}'
        return self._delete_request(cmd=cmd, params=None)

    def resetPassword(self, userId):
        cmd = f'/Users/{userId}/Password'
        data = {
            'Id': str(userId),
            'ResetPassword': True
        }
        res = self._post_request_with_token(hdr=self.token_header, cmd=cmd, data=data)

        if res.status_code == 204:
            return True
        return False

    def setUserPassword(self, userId, currentPass, newPass):
        cmd = f'/Users/{userId}/Password'
        data = {
            'Id': str(userId),
            'CurrentPw': currentPass,
            'NewPw': newPass
        }
        res = self._post_request_with_token(hdr=self.token_header, cmd=cmd, data=data)
        if res.status_code == 204:
            return True
        return False

    def updatePolicy(self, userId, policy=None):
        if not policy:
            policy = self.policy
        cmd = f'/Users/{userId}/Policy'
        res = self._post_request_with_token(hdr=self.token_header, cmd=cmd, data=policy)

        if res.status_code == 204:
            return True
        return False

    def updateConfig(self, userId, config=None):
        if not config:
            config = self.config
        cmd = f'/Users/{userId}/Configuration'
        res = self._post_request_with_token(hdr=self.token_header, cmd=cmd, data=config)

        if res.status_code == 204:
            return True
        return False

    def search(self, keyword):
        cmd = f'/Search/Hints?{urlencode({"SearchTerm": keyword})}'
        res = self._get_request_with_token(hdr=self.token_header, cmd=cmd)
        if not res:
            return []
        res = res['SearchHints']
        items = []
        for item in res:
            items.append(JellyfinItem(data=item))
        return items

    def getLibraries(self):
        cmd = f'/Users/{self.user_id}/Items'
        return self._get_request_with_token(hdr=self.token_header, cmd=cmd)

    def getUsers(self):
        cmd = '/Users'
        res = self._get_request(cmd=cmd, params=None)
        users = []
        for user in res:
            users.append(JellyfinUser(data=user))
        return users

    def updateRating(self, itemId, upvote):
        cmd = f'/Users/{self.user_id}/Items/{itemId}/Rating?Likes={upvote}'
        res = self._post_request_with_token(hdr=self.token_header, cmd=cmd)
        if res:
            return True
        return False

    def getPlaylist(self, name):
        cmd = f'/Playlists'

    def makePlaylist(self, name):
        res = self._post_request_json(
            cmd=f'/Playlists',
            payload={"Name": name, "UserId": self.user_id}
        )

        if res:
            return JellyfinPlaylist(data=res.json())
        return None

    def addToPlaylist(self, playlistId, itemIds):
        item_list = ','.join(itemIds)
        cmd = f'/Playlists/{playlistId}/Items'
        params = f'Ids={item_list}&UserId={self.user_id}'
        res = self._post_request(cmd=cmd, params=params)
        if res:
            return True
        return False

    def statsCustomQuery(self, query):
        cmd = '/user_usage_stats/submit_custom_query'
        return self._post_request(cmd=cmd, params=None, payload=query)

    def findPlexItemOnJellyfin(self, plex_item, title=None):
        if not title:
            title = plex_item.title
        results = self.search(keyword=title)
        if results:
            return results[0]
        return None
