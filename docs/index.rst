.. Libsoundtouch documentation master file, created by
   sphinx-quickstart on Sat Jun  3 11:56:19 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Libsoundtouch's documentation
=========================================

.. image:: https://api.travis-ci.org/CharlesBlonde/libsoundtouch.svg?branch=master
   :target: https://travis-ci.org/CharlesBlonde/libsoundtouch

.. image:: https://coveralls.io/repos/github/CharlesBlonde/libsoundtouch/badge.svg?branch=master
   :target: https://coveralls.io/github/CharlesBlonde/libsoundtouch?branch=master

.. image:: https://img.shields.io/pypi/v/libsoundtouch.svg
   :target: https://pypi.python.org/pypi/libsoundtouch

This Python 2.7+/3.4+ library allows you to control `Bose Soundtouch devices
<https://www.soundtouch.com/>`_ .

Features
--------

-  Discovery
-  power on/power off
-  play/pause
-  next/previous track
-  volume setting (mute/set volume/volume up/volume down)
-  repeat one/all/off
-  shuffle on/off
-  select preset (bookmark)
-  playback selected music
-  play HTTP URL (not HTTPS)
-  Multi room (zones)
-  Websocket notifications

Usage
-----

Installation
~~~~~~~~~~~~

.. code:: shell

    pip install libsoundtouch

Discovery
~~~~~~~~~

Soundtouch devices support mDNS discovery protocol.

.. code:: python

   from libsoundtouch import discover_devices

   devices = discover_devices(timeout=2)  # Default timeout is 5 seconds


   for device in devices:
       print(device.config.name + " - " + device.config.type)

Basic Usage
~~~~~~~~~~~

.. code:: python

   from libsoundtouch import soundtouch_device
   from libsoundtouch.utils import Source, Type

   device = soundtouch_device('192.168.1.1')  # Manual configuration
   device.power_on()

   # Config object
   print(device.config.name)

   # Status object
   # device.status() will do an HTTP request.
   # Try to cache this value if needed.
   status = device.status()
   print(status.source)
   print(status.artist+ " - "+ status.track)
   device.pause()
   device.next_track()
   device.play()

   # Media Playback
   # device.play_media(source, location, account, media_type)
   # account and media_type are optionals

   # Radio
   device.play_media(Source.INTERNET_RADIO, '4712') # Studio Brussel

   # Spotify
   spot_user_id = '' # Should be filled in with your Spotify userID
   # This userID can be found by playing Spotify on the
   # connected SoundTouch speaker, and calling
   # device.status().content_item.source_account
   device.play_media(Source.SPOTIFY,
      'spotify:track:5J59VOgvclrhLDYUoH5OaW',
      spot_user_id) # Bazart - Goud

   # Local music (Windows media player, Itunes)
   # Account ID can be found by playing local music on the
   # connected Soundtouch speaker, and calling
   # device.status().content_item.source_account
   account_id = device.status().content_item.source_account
   device.play_media(Source.LOCAL_MUSIC,
      'album:1',
      account_id,
      Type.ALBUM)

   # Play an HTTP URL (not HTTPS)
   device.play_url('http://fqdn/file.mp3')

   # Volume object
   # device.volume() will do an HTTP request.
   # Try to cache this value if needed.
   volume = device.volume()
   print(volume.actual)
   print(volume.muted)
   device.set_volume(30) # 0..100

   # Presets object
   # device.presets() will do an HTTP request.
   # Try to cache this value if needed.
   presets = device.presets()
   print(presets[0].name)
   print(presets[0].source)
   # Play preset 0
   device.select_preset(presets[0])

   # ZoneStatus object
   # device.zone_status() will do an HTTP request.
   # Try to cache this value if needed.
   zone_status = device.zone_status()
   print(zone_status.master_id)
   print(len(zone_status.slaves))

Multi-room
~~~~~~~~~~

Soundtouch devices supports multi-room features called zones.

.. code:: python

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

Websocket
~~~~~~~~~

Soundtouch devices support Websocket notifications in order to prevent pulling and to get immediate updates.

.. code:: python

   from libsoundtouch import soundtouch_device
   import time

   # Events listeners

   # Volume updated
   def volume_listener(volume):
       print(volume.actual)

   # Status updated
   def status_listener(status):
       print(status.track)

   # Presets updated
   def preset_listener(presets):
       for preset in presets:
           print(preset.name)

   # Zone updated
   def zone_status_listener(zone_status):
       if zone_status:
           print(zone_status.master_id)
       else:
           print('no Zone')

   device = soundtouch_device('192.168.18.1')

   device.add_volume_listener(volume_listener)
   device.add_status_listener(status_listener)
   device.add_presets_listener(preset_listener)
   device.add_zone_status_listener(zone_status_listener)

   # Start websocket thread. Not started by default
   device.start_notification()

   time.sleep(600)  # Wait for events

API Documentation
-----------------

If you are looking for information on a specific function, class, or method,
this part of the documentation is for you.

.. toctree::
   api

TODO
----

The following features are not yet implemented:

-  Better error management
-  Bass configuration


Releases
--------

.. toctree::
   versions

About Libsoundtouch
-------------------

This library has been created in order to create a component for the `Home Assistant
<https://home-assistant.io>`_ project but is totally independent.


Contributors
------------

.. include:: ../AUTHORS.rst