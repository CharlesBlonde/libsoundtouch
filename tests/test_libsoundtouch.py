# -*- coding: utf-8 -*-

import unittest
import time

import libsoundtouch
from libsoundtouch.device import NoSlavesException, NoExistingZoneException, \
    Preset, Config, SoundTouchDevice, SoundtouchInvalidUrlException
from libsoundtouch.utils import Source, Type
import logging
import codecs

try:
    from mock import Mock, mock
except ImportError:
    from unittest import mock
    from unittest.mock import Mock

from xml.dom import minidom
from requests.models import Response
import zeroconf


class MockResponse(Response):
    """Mock Soundtouch XML response."""

    def __init__(self, text):
        """Create new XML response."""

        self._content = text.encode('utf-8')
        self.encoding = None


class MockDevice(SoundTouchDevice):
    def __init__(self, host, port=8090):
        self._host = host
        self._port = port
        self._zone_status = None
        self._config = None
        self._status = None
        self._volume = None
        self._presets = None
        self._ws_port = 8080
        self._dlna_port = 8091
        self._volume_updated_listeners = []
        self._status_updated_listeners = []
        self._presets_updated_listeners = []
        self._zone_status_updated_listeners = []
        self._device_info_updated_listeners = []

    def set_base_config(self, ip, id):
        xml = """<?xml version="1.0" encoding="UTF-8" ?>
<info deviceID="%s">
    <networkInfo type="SMSC">
        <macAddress>%s</macAddress>
        <ipAddress>%s</ipAddress>
    </networkInfo>
</info>""" % (id, id, ip)
        dom = minidom.parseString(xml)
        self._config = Config(dom)
        pass


class MockPreset(Preset):
    def __init__(self, _source_xml):
        self._source_xml = _source_xml


def _mocked_device_info(*args, **kwargs):
    if args[0] == 'http://192.168.1.1:8090/info':
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<info deviceID="00112233445566">
    <name>Home</name>
    <type>SoundTouch 20</type>
    <margeAccountUUID>AccountUUIDValue</margeAccountUUID>
    <components>
        <component>
            <componentCategory>SCM</componentCategory>
            <softwareVersion>
                13.0.9.29919.1889959 epdbuild.trunk.cepeswbldXXX
            </softwareVersion>
            <serialNumber>XXXXX</serialNumber>
        </component>
        <component>
            <componentCategory>PackagedProduct</componentCategory>
            <serialNumber>YYYYY</serialNumber>
        </component>
    </components>
    <margeURL>https://streaming.bose.com</margeURL>
    <networkInfo type="SCM">
        <macAddress>00112233445566</macAddress>
        <ipAddress>192.168.1.2</ipAddress>
    </networkInfo>
    <networkInfo type="SMSC">
        <macAddress>66554433221100</macAddress>
        <ipAddress>192.168.1.1</ipAddress>
    </networkInfo>
    <moduleType>sm2</moduleType>
    <variant>spotty</variant>
    <variantMode>normal</variantMode>
    <countryCode>GB</countryCode>
    <regionCode>GB</regionCode>
</info>""")


def _mocked_device_info_without_values(*args, **kwargs):
    if args[0] == 'http://192.168.1.1:8090/info':
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<info>
    <components>
        <component>
            <componentCategory>SCM</componentCategory>
            <softwareVersion>
                13.0.9.29919.1889959 epdbuild.trunk.cepeswbldXXX
            </softwareVersion>
            <serialNumber>XXXXX</serialNumber>
        </component>
        <component>
            <componentCategory>PackagedProduct</componentCategory>
            <serialNumber>XXXXX</serialNumber>
        </component>
    </components>
    <margeURL>https://streaming.bose.com</margeURL>
    <networkInfo type="SCM">
        <macAddress>00112233445566</macAddress>
        <ipAddress>192.168.1.2</ipAddress>
    </networkInfo>
    <networkInfo type="SMSC">
        <macAddress>66554433221100</macAddress>
        <ipAddress>192.168.1.1</ipAddress>
    </networkInfo>
</info>""")


def _mocked_status_spotify(*args, **kwargs):
    if args[0] == 'http://192.168.1.1:8090/now_playing':
        codecs_open = codecs.open("tests/data/spotify.xml", "r", "utf-8")
        try:
            return MockResponse(codecs_open.read())
        finally:
            codecs_open.close()


def _mocked_status_spotify_utf8(*args, **kwargs):
    if args[0] == 'http://192.168.1.1:8090/now_playing':
        codecs_open = codecs.open("tests/data/spotify_utf8.xml", "r", "utf-8")
        try:
            return MockResponse(codecs_open.read())
        finally:
            codecs_open.close()


def _mocked_status_radio(*args, **kwargs):
    codecs_open = codecs.open("tests/data/radio.xml", "r", "utf-8")
    try:
        return MockResponse(codecs_open.read())
    finally:
        codecs_open.close()


def _mocked_status_radio_non_ascii(*args, **kwargs):
    codecs_open = codecs.open("tests/data/radio_utf8.xml", "r", "utf-8")
    try:
        return MockResponse(codecs_open.read())
    finally:
        codecs_open.close()


def _mocked_status_stored_music(*args, **kwargs):
    codecs_open = codecs.open("tests/data/stored_music.xml", "r", "utf-8")
    try:
        return MockResponse(codecs_open.read())
    finally:
        codecs_open.close()


def _mocked_status_standby(*args, **kwargs):
    if (args[0] == "http://192.168.1.1:8090/now_playing"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<nowPlaying deviceID="689E198DDB3A" source="STANDBY">
    <ContentItem source="STANDBY" isPresetable="true"/>
</nowPlaying>""")


def _mocked_volume(*args, **kwargs):
    if (args[0] == "http://192.168.1.1:8090/volume"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<volume deviceID="11223344">
    <targetvolume>26</targetvolume>
    <actualvolume>25</actualvolume>
    <muteenabled>false</muteenabled>
</volume>""")


def _mocked_play(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">PLAY</key>',
        '<key state="release" sender="Gabbo">PLAY</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_play_media_without_account(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/select" or \
                    args[1] != '<ContentItem source="INTERNET_RADIO" ' \
                               'type="uri" sourceAccount="" location="4712">' \
                               '<itemName>Select using API</itemName>' \
                               '</ContentItem>':
        raise Exception("Unknown call")


def _mocked_play_media_with_account(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/select" or \
                    args[1] != '<ContentItem source="SPOTIFY" type="uri" ' \
                               'sourceAccount="spot_user_id" ' \
                               'location="uri_track"><itemName>' \
                               'Select using API</itemName></ContentItem>':
        raise Exception("Unknown call")


def _mocked_play_media_with_type(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/select" or \
                    args[1] != '<ContentItem source="LOCAL_MUSIC" ' \
                               'type="album" sourceAccount="account_id" ' \
                               'location="album:1"><itemName>' \
                               'Select using API</itemName></ContentItem>':
        raise Exception("Unknown call")


def _mocked_pause(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">PAUSE</key>',
        '<key state="release" sender="Gabbo">PAUSE</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_play_pause(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">PLAY_PAUSE</key>',
        '<key state="release" sender="Gabbo">PLAY_PAUSE</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_play_url(*args, **kwargs):
    assert args[0] == "http://192.168.1.1:8091/AVTransport/Control"
    action = "urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"
    assert kwargs['headers']['SOAPACTION'] == action
    assert kwargs['headers']['Content-Type'] == 'text/xml; charset="utf-8"'
    assert kwargs['headers']['HOST'] == '192.168.1.1:8091'
    dom = minidom.parseString(kwargs['data'])
    url = dom.getElementsByTagName("CurrentURI")[0].firstChild.nodeValue
    assert url == "http://fqdn/file.mp3"


def _mocked_power(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">POWER</key>',
        '<key state="release" sender="Gabbo">POWER</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_set_volume(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/volume" or args[1] not in [
        '<volume>10</volume>',
    ]:
        raise Exception("Unknown call")


def _mocked_volume_up(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">VOLUME_UP</key>',
        '<key state="release" sender="Gabbo">VOLUME_UP</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_volume_down(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">VOLUME_DOWN</key>',
        '<key state="release" sender="Gabbo">VOLUME_DOWN</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_next_track(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">NEXT_TRACK</key>',
        '<key state="release" sender="Gabbo">NEXT_TRACK</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_previous_track(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">PREV_TRACK</key>',
        '<key state="release" sender="Gabbo">PREV_TRACK</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_mute(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">MUTE</key>',
        '<key state="release" sender="Gabbo">MUTE</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_repeat_one(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">REPEAT_ONE</key>',
        '<key state="release" sender="Gabbo">REPEAT_ONE</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_repeat_off(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">REPEAT_OFF</key>',
        '<key state="release" sender="Gabbo">REPEAT_OFF</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_repeat_all(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">REPEAT_ALL</key>',
        '<key state="release" sender="Gabbo">REPEAT_ALL</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_shuffle_on(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">SHUFFLE_ON</key>',
        '<key state="release" sender="Gabbo">SHUFFLE_ON</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_shuffle_off(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/key" or args[1] not in [
        '<key state="press" sender="Gabbo">SHUFFLE_OFF</key>',
        '<key state="release" sender="Gabbo">SHUFFLE_OFF</key>'
    ]:
        raise Exception("Unknown call")


def _mocked_zone_status_master(*args, **kwargs):
    if (args[0] == "http://192.168.1.1:8090/getZone"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<zone master="1111MASTER">
    <member ipaddress="192.168.1.2" role="NORMAL">1111SLAVE</member>
</zone>""")


def _mocked_zone_status_slave(*args, **kwargs):
    if (args[0] == "http://192.168.1.2:8090/getZone"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<zone master="1111MASTER" senderIPAddress="192.168.1.1"
      senderIsMaster="true">
    <member ipaddress="192.168.1.2" role="NORMAL">1111SLAVE</member>
</zone>""")


def _mocked_zone_status_none(*args, **kwargs):
    if (args[0] == "http://192.168.1.1:8090/getZone"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<zone />""")


def _mocked_presets(*args, **kwargs):
    if (args[0] == "http://192.168.1.1:8090/presets"):
        return MockResponse("""<?xml version="1.0" encoding="UTF-8" ?>
<presets>
    <preset id="1" createdOn="1476019956" updatedOn="1476019956">
        <ContentItem source="SPOTIFY" type="uri"
                     location="spotify:artist:2qxJFvFYMEDqd7ui6kSAcq"
                     sourceAccount="spotify_account" isPresetable="true">
            <itemName>Zedd</itemName>
        </ContentItem>
    </preset>
    <preset id="2">
        <ContentItem source="SPOTIFY" type="uri"
                     location="spotify:user:112233:playlist:4X7Cjisbl7340KaIh8Y1Do"
                     sourceAccount="spotify_account" isPresetable="true">
            <itemName>Afternoon Accoustic</itemName>
        </ContentItem>
    </preset>
    <preset id="3">
        <ContentItem source="SPOTIFY" type="uri"
                     location="spotify:user:332211:playlist:376GZaa2huXDHKaORSeIzP"
                     sourceAccount="spotify_account" isPresetable="true">
            <itemName>Rock Ballads</itemName>
        </ContentItem>
    </preset>
    <preset id="4">
        <ContentItem source="SPOTIFY" type="uri"
                     location="spotify:artist:2ye2Wgw4gimLv2eAKyk1NB"
                     sourceAccount="spotify_account" isPresetable="true">
            <itemName>Metallica</itemName>
        </ContentItem>
    </preset>
    <preset id="5">
        <ContentItem source="INTERNET_RADIO" location="21630" sourceAccount=""
                     isPresetable="true">
            <itemName>RMC Info Talk Sport</itemName>
        </ContentItem>
    </preset>
    <preset id="6">
        <ContentItem source="INTERNET_RADIO" location="1307" sourceAccount=""
                     isPresetable="true">
            <itemName>France Info</itemName>
        </ContentItem>
    </preset>
</presets>""")


def _mocked_select_preset(*args, **kwargs):
    if args[0] != "http://192.168.1.1:8090/select" or args[1] not in [
        '<xml>source</xml>'
    ]:
        raise Exception("Unknown call")


def _mocked_create_zone(*args, **kwargs):
    if (args[0] != "http://192.168.1.1:8090/setZone" or args[
        1] != '<zone master="1111MASTER" '
              'senderIPAddress="192.168.1.1">'
              '<member ipaddress="192.168.1.2">'
              '1111SLAVE</member></zone>'):
        raise Exception("Bad argument")


def _mocked_remove_slaves(*args, **kwargs):
    if (args[0] != 'http://192.168.1.1:8090/removeZoneSlave' or args[
        1] != '<zone master="1111MASTER">'
              '<member ipaddress="192.168.1.2">'
              '1111SLAVE</member></zone>'):
        raise Exception("Bad argument")


def _mocked_add_slaves(*args, **kwargs):
    if (args[0] != 'http://192.168.1.1:8090/addZoneSlave' or args[
        1] != '<zone master="1111MASTER">'
              '<member ipaddress="192.168.1.2">'
              '1111SLAVE</member></zone>'):
        raise Exception("Bad argument")


def _mocked_service_browser(zc, search, listener):
    assert isinstance(zc, zeroconf.Zeroconf)
    assert search == "_soundtouch._tcp.local."
    mock_zeroconf = mock.MagicMock()
    service_info = mock.MagicMock()
    service_info.port = 8090
    mock_zeroconf.get_service_info.return_value = service_info
    listener.add_service(mock_zeroconf, '', 'device.tcp')


class TestLibSoundTouch(unittest.TestCase):
    def setUp(self):  # pylint: disable=invalid-name
        """Setup things to be run when tests are started."""
        logging.disable(logging.DEBUG)

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        logging.disable(logging.NOTSET)

    @mock.patch('requests.get', side_effect=_mocked_device_info)
    def test_init_device(self, mocked_device_info):
        device = libsoundtouch.soundtouch_device("192.168.1.1")
        self.assertEqual(mocked_device_info.call_count, 1)
        self.assertEqual(device.host, "192.168.1.1")
        self.assertEqual(device.port, 8090)
        self.assertEqual(device.ws_port, 8080)
        self.assertEqual(device.dlna_port, 8091)
        self.assertEqual(device.config.device_id, "00112233445566")
        self.assertEqual(device.config.device_ip, "192.168.1.1")
        self.assertEqual(device.config.mac_address, "66554433221100")
        self.assertEqual(device.config.name, "Home")
        self.assertEqual(device.config.type, "SoundTouch 20")
        self.assertEqual(device.config.account_uuid, "AccountUUIDValue")
        self.assertEqual(device.config.module_type, "sm2")
        self.assertEqual(device.config.variant, "spotty")
        self.assertEqual(device.config.variant_mode, "normal")
        self.assertEqual(device.config.country_code, "GB")
        self.assertEqual(device.config.region_code, "GB")
        self.assertEqual(len(device.config.networks), 2)
        self.assertEqual(len(device.config.components), 2)
        self.assertListEqual(
            [component.category for component in device.config.components],
            ['SCM', 'PackagedProduct'])
        self.assertListEqual(
            [component.serial_number for component in
             device.config.components],
            ['XXXXX', 'YYYYY'])
        self.assertListEqual(
            [component.software_version for component in
             device.config.components],
            ['13.0.9.29919.1889959 epdbuild.trunk.cepeswbldXXX', None])

    @mock.patch('requests.get', side_effect=_mocked_device_info_without_values)
    def test_init_device_with_none_values(self, mocked_device_info):
        device = libsoundtouch.soundtouch_device("192.168.1.1")
        self.assertEqual(mocked_device_info.call_count, 1)
        self.assertIsNone(device.config.device_id)
        self.assertIsNone(device.config.name)
        self.assertIsNone(device.config.type)
        self.assertIsNone(device.config.account_uuid)
        self.assertIsNone(device.config.module_type)
        self.assertIsNone(device.config.variant)
        self.assertIsNone(device.config.variant_mode)
        self.assertIsNone(device.config.country_code)
        self.assertIsNone(device.config.region_code)

    @mock.patch('requests.get', side_effect=_mocked_status_spotify)
    def test_status_spotify(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(status.source, "SPOTIFY")
        self.assertEqual(status.content_item.name, "Metallica")
        self.assertEqual(status.content_item.source, "SPOTIFY")
        self.assertEqual(status.content_item.type, "uri")
        self.assertEqual(status.content_item.location,
                         "spotify:artist:2ye2Wgw4gimLv2eAKyk1NB")
        self.assertEqual(status.content_item.source_account,
                         "spotify_account")
        self.assertEqual(status.content_item.is_presetable, True)
        self.assertEqual(status.track, "Nothing Else Matters (Live)")
        self.assertEqual(status.artist, "Metallica")
        album = "Metallica Through The Never (Music from the Motion Picture)"
        self.assertEqual(status.album, album)
        image = "http://i.scdn.co/image/1362a06f43"
        self.assertEqual(status.image, image)
        self.assertEqual(status.duration, 441)
        self.assertEqual(status.position, 402)
        self.assertEqual(status.play_status, "PLAY_STATE")
        self.assertEqual(status.shuffle_setting, "SHUFFLE_OFF")
        self.assertEqual(status.repeat_setting, "REPEAT_OFF")
        self.assertEqual(status.stream_type, "TRACK_ONDEMAND")
        self.assertEqual(status.track_id,
                         "spotify:track:1HoBsGG0Ss2Wv5Ky8pkCEf")
        self.assertEqual(mocked_device_status.call_count, 1)
        # Force refresh
        self.assertEqual(device.status().source, "SPOTIFY")
        self.assertEqual(device.status().content_item.name, "Metallica")
        self.assertEqual(mocked_device_status.call_count, 3)

        # Don't refresh
        self.assertEqual(device.status(refresh=False).source, "SPOTIFY")
        self.assertEqual(device.status(refresh=False).content_item.name,
                         "Metallica")
        self.assertEqual(mocked_device_status.call_count, 3)

    @mock.patch('requests.get', side_effect=_mocked_status_spotify_utf8)
    def test_status_spotify_utf8(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(status.source, "SPOTIFY")
        self.assertEqual(status.track, u'Música Urbana')
        self.assertEqual(mocked_device_status.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_status_radio)
    def test_status_radio(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(mocked_device_status.call_count, 1)
        self.assertEqual(status.source, "INTERNET_RADIO")
        self.assertEqual(status.content_item.source, "INTERNET_RADIO")
        self.assertEqual(status.content_item.location, "21630")
        self.assertEqual(status.content_item.source_account, "")
        self.assertEqual(status.content_item.is_presetable, True)
        self.assertIsNone(status.track)
        self.assertIsNone(status.artist)
        self.assertIsNone(status.album)
        self.assertEqual(status.image,
                         "http://item.radio456.com/007452/logo/logo-21630.jpg")
        self.assertEqual(status.station_name, "RMC Info Talk Sport")
        self.assertEqual(status.description,
                         "MP3 64 kbps Paris France, Radio du sport")
        self.assertEqual(status.station_location, "Paris France")

    @mock.patch('requests.get', side_effect=_mocked_status_radio_non_ascii)
    def test_status_radio_non_ascii(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(mocked_device_status.call_count, 1)
        self.assertEqual(status.source, "INTERNET_RADIO")
        self.assertEqual(status.content_item.source, "INTERNET_RADIO")
        self.assertEqual(status.content_item.location, "1307")
        self.assertEqual(status.content_item.source_account, "")
        self.assertEqual(status.content_item.is_presetable, True)
        self.assertIsNone(status.track)
        self.assertIsNone(status.artist)
        self.assertIsNone(status.album)
        self.assertEqual(status.image,
                         "http://item.radio456.com/007452/logo/logo-1307.jpg")
        self.assertEqual(status.station_name, "France Info")
        self.assertEqual(status.station_location, "Paris France")

    @mock.patch('requests.get', side_effect=_mocked_status_stored_music)
    def test_status_stored_music(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(mocked_device_status.call_count, 1)
        self.assertEqual(status.source, "STORED_MUSIC")
        self.assertEqual(status.content_item.source, "STORED_MUSIC")
        self.assertEqual(status.content_item.location, "27$2745")
        self.assertIsNone(status.image)

    @mock.patch('requests.get', side_effect=_mocked_status_standby)
    def test_status_standby(self, mocked_device_status):
        device = MockDevice("192.168.1.1")
        status = device.status()
        self.assertEqual(mocked_device_status.call_count, 1)
        self.assertEqual(status.source, "STANDBY")
        self.assertEqual(status.content_item.source, "STANDBY")

    @mock.patch('requests.get', side_effect=_mocked_volume)
    def test_volume(self, mocked_volume):
        device = MockDevice("192.168.1.1")
        volume = device.volume()
        self.assertEqual(mocked_volume.call_count, 1)
        self.assertEqual(volume.actual, 25)
        self.assertEqual(volume.target, 26)
        self.assertEqual(volume.muted, False)

    @mock.patch('requests.post', side_effect=_mocked_play)
    def test_play(self, mocked_play):
        device = MockDevice("192.168.1.1")
        device.play()
        self.assertEqual(mocked_play.call_count, 2)

    @mock.patch('requests.post',
                side_effect=_mocked_play_media_without_account)
    def test_play_media_without_account(self, mocked_play_media):
        device = MockDevice("192.168.1.1")
        device.play_media(Source.INTERNET_RADIO, "4712")
        self.assertEqual(mocked_play_media.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_play_media_with_account)
    def test_play_media_with_account(self, mocked_play_media):
        device = MockDevice("192.168.1.1")
        device.play_media(Source.SPOTIFY, "uri_track", "spot_user_id")
        self.assertEqual(mocked_play_media.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_play_media_with_type)
    def test_play_media_with_type(self, mocked_play_media):
        device = MockDevice("192.168.1.1")
        device.play_media(Source.LOCAL_MUSIC, "album:1", "account_id",
                          Type.ALBUM)
        self.assertEqual(mocked_play_media.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_pause)
    def test_pause(self, mocked_pause):
        device = MockDevice("192.168.1.1")
        device.pause()
        self.assertEqual(mocked_pause.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_play_pause)
    def test_play_plause(self, mocked_play_pause):
        device = MockDevice("192.168.1.1")
        device.play_pause()
        self.assertEqual(mocked_play_pause.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_play_url)
    def test_play_url(self, mocked_play_url):
        device = MockDevice("192.168.1.1")
        device.play_url("http://fqdn/file.mp3")
        self.assertEqual(mocked_play_url.call_count, 1)

    def test_play_invalid_url(self):
        device = MockDevice("192.168.1.1")
        self.assertRaises(SoundtouchInvalidUrlException, device.play_url,
                          "https://fqdn/file.mp3")

    @mock.patch('libsoundtouch.SoundTouchDevice.refresh_status',
                side_effect=None)
    @mock.patch('requests.post', side_effect=_mocked_power)
    def test_power_on(self, mocked_power, refresh):
        device = MockDevice("192.168.1.1")
        device._status = Mock()
        device._status.source = "STANDBY"
        device.power_on()
        self.assertEqual(mocked_power.call_count, 2)
        self.assertEqual(refresh.call_count, 1)

    @mock.patch('libsoundtouch.SoundTouchDevice.refresh_status',
                side_effect=None)
    @mock.patch('requests.post', side_effect=_mocked_power)
    def test_power_on_if_already_on(self, mocked_power, refresh):
        device = MockDevice("192.168.1.1")
        device._status = Mock()
        device._status.source = "SPOTIFY"
        device.power_on()
        self.assertEqual(mocked_power.call_count, 0)
        self.assertEqual(refresh.call_count, 1)

    @mock.patch('libsoundtouch.SoundTouchDevice.refresh_status',
                side_effect=None)
    @mock.patch('requests.post', side_effect=_mocked_power)
    def test_power_off(self, mocked_power, refresh):
        device = MockDevice("192.168.1.1")
        device._status = Mock()
        device._status.source = "SPOTIFY"
        device.power_off()
        self.assertEqual(mocked_power.call_count, 2)
        self.assertEqual(refresh.call_count, 1)

    @mock.patch('libsoundtouch.SoundTouchDevice.refresh_status',
                side_effect=None)
    @mock.patch('requests.post', side_effect=_mocked_power)
    def test_power_off_if_already_off(self, mocked_power, refresh):
        device = MockDevice("192.168.1.1")
        device._status = Mock()
        device._status.source = "STANDBY"
        device.power_off()
        self.assertEqual(mocked_power.call_count, 0)
        self.assertEqual(refresh.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_set_volume)
    def test_set_volume(self, mocked_set_volume):
        device = MockDevice("192.168.1.1")
        device.set_volume(10)
        self.assertEqual(mocked_set_volume.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_volume_up)
    def test_volume_up(self, mocked_volume_up):
        device = MockDevice("192.168.1.1")
        device.volume_up()
        self.assertEqual(mocked_volume_up.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_volume_down)
    def test_volume_down(self, mocked_volume_down):
        device = MockDevice("192.168.1.1")
        device.volume_down()
        self.assertEqual(mocked_volume_down.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_next_track)
    def test_next_track(self, mocked_next_track):
        device = MockDevice("192.168.1.1")
        device.next_track()
        self.assertEqual(mocked_next_track.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_previous_track)
    def test_previous_track(self, mocked_previous_track):
        device = MockDevice("192.168.1.1")
        device.previous_track()
        self.assertEqual(mocked_previous_track.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_mute)
    def test_mute(self, mocked_mute):
        device = MockDevice("192.168.1.1")
        device.mute()
        self.assertEqual(mocked_mute.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_repeat_one)
    def test_repeat_one(self, mocked_repeat_one):
        device = MockDevice("192.168.1.1")
        device.repeat_one()
        self.assertEqual(mocked_repeat_one.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_repeat_all)
    def test_repeat_all(self, mocked_repeat_all):
        device = MockDevice("192.168.1.1")
        device.repeat_all()
        self.assertEqual(mocked_repeat_all.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_repeat_off)
    def test_repeat_off(self, mocked_repeat_off):
        device = MockDevice("192.168.1.1")
        device.repeat_off()
        self.assertEqual(mocked_repeat_off.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_shuffle_on)
    def test_shuffle_on(self, mocked_shuffle):
        device = MockDevice("192.168.1.1")
        device.shuffle(True)
        self.assertEqual(mocked_shuffle.call_count, 2)

    @mock.patch('requests.post', side_effect=_mocked_shuffle_off)
    def test_shuffle_off(self, mocked_shuffle):
        device = MockDevice("192.168.1.1")
        device.shuffle(False)
        self.assertEqual(mocked_shuffle.call_count, 2)

    @mock.patch('requests.get', side_effect=_mocked_presets)
    def test_presets(self, mocked_presets):
        device = MockDevice("192.168.1.1")
        presets = device.presets()
        self.assertEqual(mocked_presets.call_count, 1)
        self.assertEqual(len(presets), 6)
        self.assertEqual(presets[0].name, "Zedd")
        self.assertEqual(presets[0].preset_id, "1")
        self.assertEqual(presets[0].source, "SPOTIFY")
        self.assertEqual(presets[0].type, "uri")
        self.assertEqual(presets[0].location,
                         "spotify:artist:2qxJFvFYMEDqd7ui6kSAcq")
        self.assertEqual(presets[0].source_account, "spotify_account")
        self.assertEqual(presets[0].is_presetable, True)
        self.assertIsNotNone(presets[0].source_xml)

    @mock.patch('requests.post', side_effect=_mocked_select_preset)
    def test_select_preset(self, mocked_select_preset):
        device = MockDevice("192.168.1.1")
        preset = MockPreset("<xml>source</xml>")
        device.select_preset(preset)
        self.assertEqual(mocked_select_preset.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_zone_status_master(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        zone_status = device.zone_status()
        self.assertEqual(mocked_zone_status.call_count, 1)
        self.assertTrue(zone_status.is_master)
        self.assertEqual(zone_status.master_id, "1111MASTER")
        self.assertIsNone(zone_status.master_ip)
        self.assertEqual(len(zone_status.slaves), 1)
        self.assertEqual(zone_status.slaves[0].device_ip, "192.168.1.2")
        self.assertEqual(zone_status.slaves[0].role, "NORMAL")

    @mock.patch('requests.get', side_effect=_mocked_zone_status_slave)
    def test_zone_status_slave(self, mocked_zone_status):
        device = MockDevice("192.168.1.2")
        zone_status = device.zone_status()
        self.assertEqual(mocked_zone_status.call_count, 1)
        self.assertFalse(zone_status.is_master)
        self.assertEqual(zone_status.master_id, "1111MASTER")
        self.assertEqual(zone_status.master_ip, "192.168.1.1")
        self.assertEqual(len(zone_status.slaves), 1)
        self.assertEqual(zone_status.slaves[0].device_ip, "192.168.1.2")
        self.assertEqual(zone_status.slaves[0].role, "NORMAL")

    @mock.patch('requests.get', side_effect=_mocked_zone_status_none)
    def test_zone_status_none(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        zone_status = device.zone_status()
        self.assertEqual(mocked_zone_status.call_count, 1)
        self.assertIsNone(zone_status)

    @mock.patch('requests.post', side_effect=_mocked_create_zone)
    def test_create_zone(self, mocked_create_zone):
        device = MockDevice("192.168.1.1")
        device.set_base_config("192.168.1.1", "1111MASTER")
        device2 = MockDevice("192.168.1.2")
        device2.set_base_config("192.168.1.2", "1111SLAVE")
        device.create_zone([device2])
        self.assertEqual(mocked_create_zone.call_count, 1)

    def test_create_zone_without_master(self):
        device = MockDevice("192.168.1.1")
        self.assertRaises(NoSlavesException, device.create_zone,
                          [])

    @mock.patch('requests.post', side_effect=_mocked_remove_slaves)
    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_remove_zone_slaves(self, mocked_remove_slave, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        device.set_base_config("192.168.1.1", "1111MASTER")
        device2 = MockDevice("192.168.1.2")
        device2.set_base_config("192.168.1.2", "1111SLAVE")
        device.remove_zone_slave([device2])
        self.assertEqual(mocked_zone_status.call_count, 1)
        self.assertEqual(mocked_remove_slave.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_remove_zone_slave_without_slaves(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        self.assertRaises(NoSlavesException,
                          device.remove_zone_slave,
                          [])
        self.assertEqual(mocked_zone_status.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_zone_status_none)
    def test_remove_zone_slave_without_zone(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        self.assertRaises(NoExistingZoneException,
                          device.remove_zone_slave,
                          [])
        self.assertEqual(mocked_zone_status.call_count, 1)

    @mock.patch('requests.post', side_effect=_mocked_add_slaves)
    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_add_zone_slaves(self, mocked_add_slaves, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        device.set_base_config("192.168.1.1", "1111MASTER")
        device2 = MockDevice("192.168.1.2")
        device2.set_base_config("192.168.1.2", "1111SLAVE")
        device.add_zone_slave([device2])
        self.assertEqual(mocked_zone_status.call_count, 1)
        self.assertEqual(mocked_add_slaves.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_add_zone_slaves_without_master(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        self.assertRaises(NoSlavesException,
                          device.add_zone_slave, [])
        self.assertEqual(mocked_zone_status.call_count, 1)

    @mock.patch('requests.get', side_effect=_mocked_zone_status_none)
    def test_add_zone_slaves_without_zone(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        self.assertRaises(NoExistingZoneException,
                          device.add_zone_slave, [])
        self.assertEqual(mocked_zone_status.call_count, 1)

    @mock.patch('websocket.WebSocketApp.run_forever')
    def test_ws_start(self, ws_run_forever):
        device = MockDevice("192.168.1.1")
        device.start_notification()
        time.sleep(1)  # Wait thread start
        self.assertEqual(ws_run_forever.call_count, 1)

    def test_ws_listeners(self):
        device = MockDevice("192.168.1.1")

        def listener_1():
            pass

        def listener_2():
            pass

        device.add_volume_listener(listener_1)
        device.add_volume_listener(listener_2)
        self.assertEqual(len(device.volume_updated_listeners), 2)
        device.remove_volume_listener(listener_2)
        self.assertEqual(len(device.volume_updated_listeners), 1)
        device.clear_volume_listeners()
        self.assertEqual(len(device.volume_updated_listeners), 0)

        device.add_status_listener(listener_1)
        device.add_status_listener(listener_2)
        self.assertEqual(len(device.status_updated_listeners), 2)
        device.remove_status_listener(listener_2)
        self.assertEqual(len(device.status_updated_listeners), 1)
        device.clear_status_listener()
        self.assertEqual(len(device.status_updated_listeners), 0)

        device.add_presets_listener(listener_1)
        device.add_presets_listener(listener_2)
        self.assertEqual(len(device.presets_updated_listeners), 2)
        device.remove_presets_listener(listener_2)
        self.assertEqual(len(device.presets_updated_listeners), 1)
        device.clear_presets_listeners()
        self.assertEqual(len(device.presets_updated_listeners), 0)

        device.add_zone_status_listener(listener_1)
        device.add_zone_status_listener(listener_2)
        self.assertEqual(len(device.zone_status_updated_listeners), 2)
        device.remove_zone_status_listener(listener_2)
        self.assertEqual(len(device.zone_status_updated_listeners), 1)
        device.clear_zone_status_listeners()
        self.assertEqual(len(device.zone_status_updated_listeners), 0)

        device.add_device_info_listener(listener_1)
        device.add_device_info_listener(listener_2)
        self.assertEqual(len(device.device_info_updated_listeners), 2)
        device.remove_device_info_listener(listener_2)
        self.assertEqual(len(device.device_info_updated_listeners), 1)
        device.clear_device_info_listeners()
        self.assertEqual(len(device.device_info_updated_listeners), 0)

    def test_ws_status_notification(self):
        device = MockDevice("192.168.1.1")
        self.listener_called = False
        self.status = None

        def listener(status_msg):
            self.listener_called = True
            self.status = status_msg

        device.add_status_listener(listener)
        codecs_open = codecs.open("tests/data/ws_status.xml", "r", "utf-8")
        try:
            content = codecs_open.read()
            device._on_message(None, content)
            self.assertTrue(self.listener_called)
            self.assertEqual(self.status.source, "SPOTIFY")
            self.assertEqual(self.status.track, "Devil We Know")
        finally:
            codecs_open.close()

    def test_ws_volume_notification(self):
        device = MockDevice("192.168.1.1")
        self.listener_called = False
        self.volume = None

        def listener(status_msg):
            self.listener_called = True
            self.volume = status_msg

        device.add_volume_listener(listener)
        codecs_open = codecs.open("tests/data/ws_volume.xml", "r", "utf-8")
        try:
            content = codecs_open.read()
            device._on_message(None, content)
            self.assertTrue(self.listener_called)
            self.assertEqual(self.volume.actual, 21)
        finally:
            codecs_open.close()

    def test_ws_presets_notification(self):
        device = MockDevice("192.168.1.1")
        self.listener_called = False
        self.presets = None

        def listener(status_msg):
            self.listener_called = True
            self.presets = status_msg

        device.add_presets_listener(listener)
        codecs_open = codecs.open("tests/data/ws_presets.xml", "r", "utf-8")
        try:
            content = codecs_open.read()
            device._on_message(None, content)
            self.assertTrue(self.listener_called)
            self.assertEqual(len(self.presets), 3)
            self.assertEqual(self.presets[0].name, "Zedd")
        finally:
            codecs_open.close()

    @mock.patch('requests.get', side_effect=_mocked_zone_status_master)
    def test_ws_zone_notification(self, mocked_zone_status):
        device = MockDevice("192.168.1.1")
        self.listener_called = False
        self.zone = None

        def listener(status_msg):
            self.listener_called = True
            self.zone = status_msg

        device.add_zone_status_listener(listener)
        codecs_open = codecs.open("tests/data/ws_zone.xml", "r", "utf-8")
        try:
            content = codecs_open.read()
            device._on_message(None, content)
            self.assertTrue(self.listener_called)
            self.assertEqual(mocked_zone_status.call_count, 1)
            self.assertTrue(self.zone.is_master)
            self.assertEqual(self.zone.master_id, "1111MASTER")
        finally:
            codecs_open.close()

    @mock.patch('requests.get', side_effect=_mocked_device_info)
    def test_ws_info_notification(self, mocked_device_info):
        device = MockDevice("192.168.1.1")
        self.listener_called = False
        self.info = None

        def listener(status_msg):
            self.listener_called = True
            self.info = status_msg

        device.add_device_info_listener(listener)
        codecs_open = codecs.open("tests/data/ws_info.xml", "r", "utf-8")
        try:
            content = codecs_open.read()
            device._on_message(None, content)
            self.assertTrue(self.listener_called)
            self.assertEqual(mocked_device_info.call_count, 1)
            self.assertEqual(self.info.name, "Home")
        finally:
            codecs_open.close()

    @mock.patch('requests.get', side_effect=_mocked_device_info)
    @mock.patch('socket.inet_ntoa', return_value='192.168.1.1')
    @mock.patch('zeroconf.ServiceBrowser.__init__', return_value=None,
                side_effect=_mocked_service_browser)
    def test_discover_devices(self, mocked_service_browser, mocked_inet_ntoa,
                              mocked_request_get):
        devices = libsoundtouch.discover_devices(timeout=1)
        self.assertEqual(mocked_service_browser.call_count, 1)
        self.assertEqual(mocked_inet_ntoa.call_count, 1)
        self.assertEqual(mocked_request_get.call_count, 1)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].host, "192.168.1.1")
        self.assertEqual(devices[0].port, 8090)
