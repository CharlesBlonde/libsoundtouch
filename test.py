from libsoundtouch import soundtouch_device, Key, Source

device = soundtouch_device('192.168.0.102')

def play_from_TuneIn():
    device.init_play(Source.INTERNET_RADIO, '', '4712') # Studio Brussels

def play_from_Spotify():
    spot_user_id = ""
    track_id = 'spotify:track:5J59VOgvclrhLDYUoH5OaW' # Bazart - Goud
    device.init_play(Source.SPOTIFY, spot_user_id, track_id)

device.power_on()
device.set_volume(20)
play_from_TuneIn()