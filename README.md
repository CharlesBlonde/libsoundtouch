# Bose Soundtouch Python library

[![Build Status](https://travis-ci.org/CharlesBlonde/libsoundtouch.svg?branch=master)](https://travis-ci.org/CharlesBlonde/libsoundtouch) [![Coverage Status](https://coveralls.io/repos/github/CharlesBlonde/libsoundtouch/badge.svg?branch=master)](https://coveralls.io/github/CharlesBlonde/libsoundtouch?branch=master)

This Python 2.7+/3.4+ library allows you to control [Bose Soundtouch devices](https://www.soundtouch.com/).

This library has been created in order to create a component for the [Home Assistant](https://home-assistant.io/) project but is totally independent.

## How to use it ?


```shell
pip install libsoundtouch
```

```python
from libsoundtouch import soundtouch_device
from libsoundtouch.utils import Source

device = soundtouch_device('192.168.1.1')
device.power_on()

# Config object
print(device.config.name)

# Status object
# device.status() will do an HTTP request. Try to cache this value if needed.
status = device.status()
print(status.source)
print(status.artist+ " - "+ status.track)
device.pause()
device.next_track()
device.play()

# Media Playback
# device.play_media(source, location, account) #account is optional
device.play_media(Source.INTERNET_RADIO, '4712') # Studio Brussel
spot_user_id = '' # Should be filled in with your Spotify userID
# This userID can be found by playing Spotify on the connected SoundTouch speaker, and calling
# device.status().content_item.source_account
device.play_media(Source.SPOTIFY, 'spotify:track:5J59VOgvclrhLDYUoH5OaW', spot_user_id) # Bazart - Goud

# Volume object
# device.volume() will do an HTTP request. Try to cache this value if needed.
volume = device.volume()
print(volume.actual)
print(volume.muted)
device.set_volume(30) # 0..100

# Presets object
# device.presets() will do an HTTP request. Try to cache this value if needed.
presets = device.presets()
print(presets[0].name)
print(presets[0].source)
# Play preset 0
device.select_preset(presets[0])

# ZoneStatus object
# device.zone_status() will do an HTTP request. Try to cache this value if needed.
zone_status = device.zone_status()
print(zone_status.master_id)
print(len(zone_status.slaves))
```

## Supported features

### Basics commands

* power on/power off
* play/pause
* next/previous track
* volume setting (mute/set volume/volume up/volume down)
* repeat one/all/off
* shuffle on/off
* select preset (bookmark)
* playback selected music

### Multi-room

Soundtouch devices supports multi-room features called zones.

```python
from libsoundtouch import soundtouch_device

master = soundtouch_device('192.168.18.1')
slave1 = soundtouch_device('192.168.18.2')
slave2 = soundtouch_device('192.168.18.3')

# Create a new zone
master.create_zone([slave1, slave2])

# Remove a slave
master.remove_zone_slave([slave2])

# Add a slave
master.add_zone_slave([slave2])
```

## Incoming features

The following features are not yet implemented:

* Auto discovery: Soundtouch devices supports SSDP and MDNS auto discovery protocols. Tests has been done but not yet implemented
* Web sockets: Web sockets are supported in order to register to get devices updates without manual refreshing.

## Access to the official API documentation

For an unknown reason, the API documentation is not freely available but you can request to get it: http://developers.bose.com/.
You have to sent an email and you'll received a response in a minute with 2 PDF:
* SoundTouchAPI_Discovery.pdf: How to use SSDP and MDNS discovery protocols
* SoundTouchAPI_WebServices.pdf: REST API documentation. Be carefull, the documenation contains errors and is not fully up to date
