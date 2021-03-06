import urllib2
import json
import datetime

import const

class LMSQuery():
    def __init__(self, host=const.LMS_HOST, port=const.LMS_PORT, player_id=""):
        self.host = host
        self.port = port
        self.server_url = "http://%s:%s/jsonrpc.js" % (self.host, self.port)
        self.player_id = player_id

    # Generic query
    def query(self, player_id="", *args):
        params = json.dumps({'id':1, 'method':'slim.request',
                             'params':[player_id, list(args)]})
        req = urllib2.Request(self.server_url, params)
        response = urllib2.urlopen(req)
        response_txt = response.read()
        return json.loads(response_txt)['result']
    
    # Server commands
    def rescan(self):
        return self.query("", "rescan")

    def get_server_status(self):
        return self.query("", "serverstatus", 0, 99)
    
    def get_artists(self):
        return self.query("", "artists", 0, 9999)['artists_loop']
        
    def get_artist_count(self):
        return len(self.get_artists())
    
    def get_radios_count(self):
        return self.query("", "favorites", "items")['count']

    def get_player_count(self):
        return self.query("", "player", "count", "?")['_count']

    def get_players(self):
        players = self.get_server_status()
        if len(players):
            players = players['players_loop']
        return players

    
    # Player commands
    def set_power(self, player_id, power = 1):
        self.query(player_id, "power", power)

    def set_power_all(self, power = 1):
        players = self.get_players()
        for player in players:
            self.set_power(player['playerid'], power)

    def play_album(self, player_id, id):
        return self.query(player_id, "playlistcontrol", "cmd:load",
                          "album_id:"+str(id))
        
    def play_radio(self, player_id, radio):
        return self.query(player_id, "favorites", "playlist", "play",
                          "item_id:"+str(radio))
    
    def pause(self, player_id):
        return self.query(player_id, "pause")
    
    def skip_songs(self, player_id, amount = 1):
        if amount > 0:
            amount = "+" + str(amount)
        else:
            amount = str(amount)
        return self.query(player_id, "playlist", "index", amount)
    
    def previous_song(self, player_id):
        return self.skip_songs(player_id, -1)

    def next_song(self, player_id):
        return self.skip_songs(player_id)
    
    def get_volume(self, player_id):
        volume = self.query(player_id, "mixer", "volume", "?")
        if len(volume):
            volume = volume['_volume']
        else:
            volume = 0
        return volume
        
    def set_volume(self, player_id, volume):
        self.query(player_id, "mixer", "volume", volume)

    def get_current_song_title(self, player_id):
        title = self.query(player_id, "current_title", "?")
        if len(title):
            title = title['_current_title']
        else:
            title = ""
        return title

    def get_current_artist(self, player_id):
        artist = self.query(player_id, "artist", "?")
        if len(artist):
            artist = artist['_artist']
        else:
            artist = ""
        return artist

    def get_current_album(self, player_id):
        album = self.query(player_id, "album", "?")
        if len(album):
            album = album['_album']
        else:
            album = ""
        return album

    def get_current_title(self, player_id):
        title = self.query(player_id, "title", "?")
        if len(title):
            title = title['_title']
        else:
            title = ""
        return title

    def get_current_radio_title(self, player_id, radio):
        return self.query(player_id, "favorites",
                          "items", 0, 99)['loop_loop'][radio]['name']

    def get_artist_album(self, player_id, artist_id):
        return self.query(player_id, "albums", 0, 99, "tags:al",
                          "artist_id:"+str(artist_id))['albums_loop']
    
    def get_alarms(self, player_id, enabled=True):
        if enabled:
            alarmsEnabled = self.get_player_pref(player_id, "alarmsEnabled")
            if alarmsEnabled == "0":
                return {}
            filter = "enabled"
        else:
            filter = "all"
        return self.query(player_id, "alarms", 0, 99, "filter:%s" % filter)

    def get_next_alarm(self, player_id):
        alarms = self.get_alarms(player_id)
        alarmtime = 0
        delta = 0
        if alarms == {} or alarms['count'] == 0:
            return {}
        for alarmitem in alarms['alarms_loop']:
            if(str((datetime.datetime.today().weekday() + 1) % 7)
               not in alarmitem['dow']):
                continue
            alarmtime_new = datetime.timedelta(seconds=int(alarmitem['time']))
            now = datetime.datetime.now()
            currenttime = datetime.timedelta(hours=now.hour,
                                             minutes=now.minute,
                                             seconds=now.second)
            delta_new = alarmtime_new - currenttime
            if delta == 0:
                delta = delta_new
                alarmtime = alarmtime_new
            elif delta_new < delta:
                delta = delta_new
                alarmtime = alarmtime_new
        if alarmtime == 0:
            return {}
        else:
            return { "alarmtime" : alarmtime.seconds, "delta" : delta.seconds }

    def get_player_pref(self, player_id, pref):
        return self.query(player_id, "playerpref", pref, "?")['_p2']

    def set_player_pref(self, player_id, pref, value):
        self.query(player_id, "playerpref", pref, value)
    
    def display(self, player_id, line1, line2, duration = 5):
        self.query(player_id, "display", line1, line2, duration)
        
    def display_all(self, line1, line2, duration = 5):
        players = self.get_players()
        for player in players:
            self.display(player['playerid'], line1, line2, duration)
        