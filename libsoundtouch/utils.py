"""Utils for the Bose Soundtouch Device."""

import logging
import socket

from enum import Enum

_LOGGER = logging.getLogger(__name__)


class Key(Enum):
    """Keys of the device."""

    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    PLAY_PAUSE = 'PLAY_PAUSE'
    STOP = 'STOP'
    PREV_TRACK = 'PREV_TRACK'
    NEXT_TRACK = 'NEXT_TRACK'
    THUMBS_UP = 'THUMBS_UP'
    THUMBS_DOWN = 'THUMBS_DOWN'
    BOOKMARK = 'BOOKMARK'
    POWER = 'POWER'
    MUTE = 'MUTE'
    VOLUME_UP = 'VOLUME_UP'
    VOLUME_DOWN = 'VOLUME_DOWN'
    PRESET_1 = 'PRESET_1'
    PRESET_2 = 'PRESET_2'
    PRESET_3 = 'PRESET_3'
    PRESET_4 = 'PRESET_4'
    PRESET_5 = 'PRESET_5'
    PRESET_6 = 'PRESET_6'
    AUX_INPUT = 'AUX_INPUT'
    SHUFFLE_OFF = 'SHUFFLE_OFF'
    SHUFFLE_ON = 'SHUFFLE_ON'
    REPEAT_OFF = 'REPEAT_OFF'
    REPEAT_ONE = 'REPEAT_ONE'
    REPEAT_ALL = 'REPEAT_ALL'
    ADD_FAVORITE = 'ADD_FAVORITE'
    REMOVE_FAVORITE = 'REMOVE_FAVORITE'


class Source(Enum):
    """Music sources supported by the device."""

    SLAVE_SOURCE = "SLAVE_SOURCE"
    INTERNET_RADIO = "INTERNET_RADIO"
    PANDORA = "PANDORA"
    AIRPLAY = "AIRPLAY"
    STORED_MUSIC = "STORED_MUSIC"
    AUX = "AUX"
    OFF_SOURCE = "OFF_SOURCE"
    CURRATED_RADIO = "CURRATED_RADIO"
    STANDBY = "STANDBY"
    UPDATE = "UPDATE"
    DEEZER = "DEEZER"
    SPOTIFY = "SPOTIFY"
    IHEART = "IHEART"
    LOCAL_MUSIC = "LOCAL_MUSIC"
    BLUETOOTH = "BLUETOOTH"


class Type(Enum):
    """Music types.

    URI for streaming (Spotify, NAS, etc)
    TRACK/ALBUM/PLAYLIST for music libraries on computer (Windows media player,
    Itunes)
    """

    URI = "uri"
    TRACK = "track"
    ALBUM = "album"
    PLAYLIST = "playlist"


class SoundtouchDeviceListener(object):
    """Message listener."""

    def __init__(self, add_device_function):
        """Create a new message listener.

        :param add_device_function: Callback function
        """
        self.add_device_function = add_device_function

    def remove_service(self, zeroconf, device_type, name):
        # pylint: disable=unused-argument,no-self-use
        """Remove listener."""
        _LOGGER.info("Service %s removed", name)

    def add_service(self, zeroconf, device_type, name):
        """Add device.

        :param zeroconf: MSDNS object
        :param device_type: Service type
        :param name: Device name
        """
        device_name = (name.split(".")[0])
        info = zeroconf.get_service_info(device_type, name)
        address = socket.inet_ntoa(info.address)
        self.add_device_function(device_name, address, info.port)
