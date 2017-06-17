"""Bose Soundtouch Device."""

# pylint: disable=too-many-public-methods,too-many-instance-attributes,
# pylint: disable=useless-super-delegation,too-many-lines

import logging
from threading import Thread
from xml.dom import minidom

import requests
import websocket

from .utils import Key, Type

STATE_STANDBY = 'STANDBY'

_LOGGER = logging.getLogger(__name__)


def _get_dom_attribute(xml_dom, attribute, default_value=None):
    if attribute in xml_dom.attributes.keys():
        return xml_dom.attributes[attribute].value
    return default_value


def _get_dom_element_attribute(xml_dom, element, attribute,
                               default_value=None):
    element = _get_dom_element(xml_dom, element)
    if element is not None:
        if attribute in element.attributes.keys():
            return element.attributes[attribute].value
        return None
    else:
        return default_value


def _get_dom_elements(xml_dom, element):
    return xml_dom.getElementsByTagName(element)


def _get_dom_element(xml_dom, element):
    elements = _get_dom_elements(xml_dom, element)
    if elements:
        return elements[0]
    return None


def _get_dom_element_value(xml_dom, element, default_value=None):
    element = _get_dom_element(xml_dom, element)
    if element is not None and element.firstChild is not None:
        return element.firstChild.nodeValue.strip()
    return default_value


class WebSocketThread(Thread):
    """Websocket thread."""

    def __init__(self, ws):
        """Create new Websocket thread."""
        Thread.__init__(self)
        self._ws = ws

    def run(self):
        """Start Websocket thread."""
        self._ws.run_forever()


class SoundTouchDevice:
    """Bose SoundTouch Device."""

    @staticmethod
    def __run_listener(listeners, value):
        """Run Listener with value."""
        for listener in listeners:
            listener(value)

    def _on_message(self, web_socket, message):
        # pylint: disable=unused-argument
        """Call when web socket is received."""
        dom = minidom.parseString(message.encode('utf-8'))
        if dom.firstChild.nodeName == "updates":
            action_node = dom.firstChild.firstChild
            action = action_node.nodeName
            if action == "volumeUpdated":
                self._volume = Volume(action_node.firstChild)
                self.__run_listener(self._volume_updated_listeners,
                                    self._volume)
            if action == "nowPlayingUpdated":
                self._status = Status(action_node.firstChild)
                self.__run_listener(self._status_updated_listeners,
                                    self._status)
            if action == "presetsUpdated" and action_node.hasChildNodes():
                self._presets = []
                for preset in _get_dom_elements(dom, "preset"):
                    self._presets.append(Preset(preset))
                self.__run_listener(self._presets_updated_listeners,
                                    self._presets)
            if action == "zoneUpdated":
                self.__run_listener(self._zone_status_updated_listeners,
                                    self.zone_status(True))
            if action == "infoUpdated":
                self.__init_config()
                self.__run_listener(self._device_info_updated_listeners,
                                    self._config)

    def __init__(self, host, port=8090, ws_port=8080):
        """Create a new Soundtouch device.

        :param host: Host of the device
        :param port: Port of the device. Default 8090
        :param ws_port: Web socket port. Default 8080

        """
        self._host = host
        self._port = port
        self._ws_port = ws_port
        self.__init_config()
        self._status = None
        self._volume = None
        self._zone_status = None
        self._presets = None
        self._ws_client = None
        self._volume_updated_listeners = []
        self._status_updated_listeners = []
        self._presets_updated_listeners = []
        self._zone_status_updated_listeners = []
        self._device_info_updated_listeners = []

    def __init_config(self):
        response = requests.get(
            "http://" + self._host + ":" + str(self._port) + "/info")
        dom = minidom.parseString(response.text)
        self._config = Config(dom)

    def start_notification(self):
        """Start Websocket connection."""
        self._ws_client = websocket.WebSocketApp(
            "ws://{0}:{1}/".format(self._host, self._ws_port),
            on_message=self._on_message,
            subprotocols=['gabbo'])
        ws_thread = WebSocketThread(self._ws_client)
        ws_thread.start()

    def add_volume_listener(self, listener):
        """Add a new volume updated listener."""
        self._volume_updated_listeners.append(listener)

    def add_status_listener(self, listener):
        """Add a new status updated listener."""
        self._status_updated_listeners.append(listener)

    def add_presets_listener(self, listener):
        """Add a new presets updated listener."""
        self._presets_updated_listeners.append(listener)

    def add_zone_status_listener(self, listener):
        """Add a new zone status updated listener."""
        self._zone_status_updated_listeners.append(listener)

    def add_device_info_listener(self, listener):
        """Add a new device info updated listener."""
        self._device_info_updated_listeners.append(listener)

    def remove_volume_listener(self, listener):
        """Remove a new volume updated listener."""
        if listener in self._volume_updated_listeners:
            self._volume_updated_listeners.remove(listener)

    def remove_status_listener(self, listener):
        """Remove a new status updated listener."""
        if listener in self._status_updated_listeners:
            self._status_updated_listeners.remove(listener)

    def remove_presets_listener(self, listener):
        """Remove a new presets updated listener."""
        if listener in self._presets_updated_listeners:
            self._presets_updated_listeners.remove(listener)

    def remove_zone_status_listener(self, listener):
        """Remove a new zone status updated listener."""
        if listener in self._zone_status_updated_listeners:
            self._zone_status_updated_listeners.remove(listener)

    def remove_device_info_listener(self, listener):
        """Remove a new device info updated listener."""
        if listener in self._device_info_updated_listeners:
            self._device_info_updated_listeners.remove(listener)

    def clear_volume_listeners(self):
        """Clear volume updated listeners."""
        del self._volume_updated_listeners[:]

    def clear_status_listener(self):
        """Clear status updated listeners."""
        del self._status_updated_listeners[:]

    def clear_presets_listeners(self):
        """Clear presets updated listeners."""
        del self._presets_updated_listeners[:]

    def clear_zone_status_listeners(self):
        """Clear zone status updated listeners."""
        del self._zone_status_updated_listeners[:]

    def clear_device_info_listeners(self):
        """Clear device info updated listener.."""
        del self._device_info_updated_listeners[:]

    @property
    def volume_updated_listeners(self):
        """Return Volume Updated listeners."""
        return self._volume_updated_listeners

    @property
    def status_updated_listeners(self):
        """Return Status Updated listeners."""
        return self._status_updated_listeners

    @property
    def presets_updated_listeners(self):
        """Return Presets Updated listeners."""
        return self._presets_updated_listeners

    @property
    def zone_status_updated_listeners(self):
        """Return Zone Status Updated listeners."""
        return self._zone_status_updated_listeners

    @property
    def device_info_updated_listeners(self):
        """Return Device Info Updated listeners."""
        return self._device_info_updated_listeners

    def refresh_status(self):
        """Refresh status state."""
        response = requests.get(
            "http://" + self._host + ":" + str(self._port) + "/now_playing")
        response.encoding = 'UTF-8'
        dom = minidom.parseString(response.text.encode('utf-8'))
        self._status = Status(dom)

    def refresh_volume(self):
        """Refresh volume state."""
        response = requests.get(
            "http://" + self._host + ":" + str(self._port) + "/volume")
        dom = minidom.parseString(response.text)
        self._volume = Volume(dom)

    def refresh_presets(self):
        """Refresh presets."""
        response = requests.get(
            "http://" + self._host + ":" + str(self._port) + "/presets")
        dom = minidom.parseString(response.text)
        self._presets = []
        for preset in _get_dom_elements(dom, "preset"):
            self._presets.append(Preset(preset))

    def refresh_zone_status(self):
        """Refresh Zone Status."""
        response = requests.get(
            "http://" + self._host + ":" + str(self._port) + "/getZone")
        dom = minidom.parseString(response.text)
        if _get_dom_elements(dom, "member"):
            self._zone_status = ZoneStatus(dom)
        else:
            self._zone_status = None

    def select_preset(self, preset):
        """Play selected preset.

        :param preset Selected preset.
        """
        requests.post(
            'http://' + self._host + ":" + str(self._port) + '/select',
            preset.source_xml)

    def _create_zone(self, slaves):
        if len(slaves) <= 0:
            raise NoSlavesException()
        request_body = '<zone master="%s" senderIPAddress="%s">' % (
            self.config.device_id, self.config.device_ip
        )
        for slave in slaves:
            request_body += '<member ipaddress="%s">%s</member>' % (
                slave.config.device_ip, slave.config.device_id)
        request_body += '</zone>'
        return request_body

    def _get_zone_request_body(self, slaves):
        if len(slaves) <= 0:
            raise NoSlavesException()
        request_body = '<zone master="%s">' % self.config.device_id
        for slave in slaves:
            request_body += '<member ipaddress="%s">%s</member>' % (
                slave.config.device_ip, slave.config.device_id)
        request_body += '</zone>'
        return request_body

    def create_zone(self, slaves):
        """Create a zone (multi-room) on a master and play on specified slaves.

        :param slaves: List of slaves. Can not be empty

        """
        request_body = self._create_zone(slaves)
        _LOGGER.info("Creating multi-room zone with master device %s",
                     self.config.name)
        requests.post("http://" + self.host + ":" + str(
            self.port) + "/setZone",
                      request_body)

    def add_zone_slave(self, slaves):
        """
        Add slave(s) to and existing zone (multi-room).

        Zone must already exist and slaves array can not be empty.

        :param slaves: List of slaves. Can not be empty
        """
        if self.zone_status() is None:
            raise NoExistingZoneException()
        request_body = self._get_zone_request_body(slaves)
        _LOGGER.info("Adding slaves to multi-room zone with master device %s",
                     self.config.name)
        requests.post(
            "http://" + self.host + ":" + str(
                self.port) + "/addZoneSlave",
            request_body)

    def remove_zone_slave(self, slaves):
        """
        Remove slave(s) from and existing zone (multi-room).

        Zone must already exist and slaves list can not be empty.
        Note: If removing last slave, the zone will be deleted and you'll have
        to create a new one. You will not be able to add a new slave anymore.

        :param slaves: List of slaves to remove

        """
        if self.zone_status() is None:
            raise NoExistingZoneException()
        request_body = self._get_zone_request_body(slaves)
        _LOGGER.info("Removing slaves from multi-room zone with master " +
                     "device %s", self.config.name)
        requests.post(
            "http://" + self.host + ":" + str(
                self.port) + "/removeZoneSlave", request_body)

    def _send_key(self, key):
        action = '/key'
        press = '<key state="press" sender="Gabbo">%s</key>' % key
        release = '<key state="release" sender="Gabbo">%s</key>' % key
        requests.post('http://' + self._host + ":" +
                      str(self._port) + action, press)
        requests.post('http://' + self._host + ":" +
                      str(self._port) + action, release)

    def play_media(self, source, location, source_acc=None,
                   media_type=Type.URI):
        """
        Start music playback from a chosen source.

        :param source: Source from which to play. Elements of Source enum.
        :param location: A unique uri or identifier. Represents the
            requested music from the source.
        :param source_acc: Source account. Imperative for some sources.
            For Spotify, this can be found by playing Spotify on the connected
            SoundTouch speaker, and calling:
            device.status().content_item.source_account
        :param media_type: Type of the requested music. Typical values are:
            "uri", "track", "album", "playlist". This can be found in
            device.status().content_item.type
        """
        action = "/select"
        play = '<ContentItem source="%s" type="%s" sourceAccount="%s" ' \
               'location="%s"><itemName>Select using API</itemName>' \
               '</ContentItem>' % (
                   source.value, media_type.value,
                   source_acc if source_acc else '', location)
        requests.post('http://' + self._host + ":" +
                      str(self._port) + action, play)

    @property
    def host(self):
        """Host of the device."""
        return self._host

    @property
    def port(self):
        """Return API port of the device."""
        return self._port

    @property
    def config(self):
        """Get config object."""
        return self._config

    def status(self, refresh=True):
        """Get status object.

        :param refresh: Force refresh, else return old data.
        """
        if self._status is None or refresh:
            self.refresh_status()
        return self._status

    def volume(self, refresh=True):
        """Get volume object.

        :param refresh: Force refresh, else return old data.
        """
        if self._volume is None or refresh:
            self.refresh_volume()
        return self._volume

    def zone_status(self, refresh=True):
        """Get Zone Status.

        :param refresh: Force refresh, else return old data.
        """
        if self._zone_status is None or refresh:
            self.refresh_zone_status()
        return self._zone_status

    def presets(self, refresh=True):
        """Presets.

        :param refresh: Force refresh, else return old data.
        """
        if self._presets is None or refresh:
            self.refresh_presets()
        return self._presets

    def set_volume(self, level):
        """Set volume level: from 0 to 100."""
        action = '/volume'
        volume = '<volume>%s</volume>' % level
        requests.post('http://' + self._host + ":" + str(self._port) + action,
                      volume)

    def mute(self):
        """Mute/Un-mute volume."""
        self._send_key(Key.MUTE.value)

    def volume_up(self):
        """Volume up."""
        self._send_key(Key.VOLUME_UP.value)

    def volume_down(self):
        """Volume down."""
        self._send_key(Key.VOLUME_DOWN.value)

    def next_track(self):
        """Switch to next track."""
        self._send_key(Key.NEXT_TRACK.value)

    def previous_track(self):
        """Switch to previous track."""
        self._send_key(Key.PREV_TRACK.value)

    def pause(self):
        """Pause."""
        self._send_key(Key.PAUSE.value)

    def play(self):
        """Play."""
        self._send_key(Key.PLAY.value)

    def play_pause(self):
        """Toggle play status."""
        self._send_key(Key.PLAY_PAUSE.value)

    def repeat_off(self):
        """Turn off repeat."""
        self._send_key(Key.REPEAT_OFF.value)

    def repeat_one(self):
        """Repeat one. Doesn't work."""
        self._send_key(Key.REPEAT_ONE.value)

    def repeat_all(self):
        """Repeat all."""
        self._send_key(Key.REPEAT_ALL.value)

    def shuffle(self, shuffle):
        """Shuffle on/off.

        :param shuffle: Boolean on/off
        """
        if shuffle:
            self._send_key(Key.SHUFFLE_ON.value)
        else:
            self._send_key(Key.SHUFFLE_OFF.value)

    def power_on(self):
        """Power on device."""
        if self.status().source == STATE_STANDBY:
            self._send_key(Key.POWER.value)

    def power_off(self):
        """Power off device."""
        if self.status().source != STATE_STANDBY:
            self._send_key(Key.POWER.value)


class Config:
    """Soundtouch device configuration."""

    def __init__(self, xml_dom):
        """Create a new configuration.

        :param xml_dom: Configuration XML DOM
        """
        self._id = _get_dom_element_attribute(xml_dom, "info", "deviceID")
        self._name = _get_dom_element_value(xml_dom, "name")
        self._type = _get_dom_element_value(xml_dom, "type")
        self._account_uuid = _get_dom_element_value(xml_dom,
                                                    "margeAccountUUID")
        self._module_type = _get_dom_element_value(xml_dom, "moduleType")
        self._variant = _get_dom_element_value(xml_dom, "variant")
        self._variant_mode = _get_dom_element_value(xml_dom, "variantMode")
        self._country_code = _get_dom_element_value(xml_dom, "countryCode")
        self._region_code = _get_dom_element_value(xml_dom, "regionCode")
        self._networks = []
        for network in xml_dom.getElementsByTagName("networkInfo"):
            self._networks.append(Network(network))
        self._components = []
        for components in _get_dom_elements(xml_dom, "components"):
            for component in _get_dom_elements(components, "component"):
                self._components.append(Component(component))

    @property
    def device_id(self):
        """Device ID."""
        return self._id

    @property
    def name(self):
        """Device name."""
        return self._name

    @property
    def type(self):
        """Device type."""
        return self._type

    @property
    def networks(self):
        """Network."""
        return self._networks

    @property
    def components(self):
        """Components."""
        return self._components

    @property
    def account_uuid(self):
        """Account UUID."""
        return self._account_uuid

    @property
    def module_type(self):
        """Return module type."""
        return self._module_type

    @property
    def variant(self):
        """Variant."""
        return self._variant

    @property
    def variant_mode(self):
        """Variant mode."""
        return self._variant_mode

    @property
    def country_code(self):
        """Country code."""
        return self._country_code

    @property
    def region_code(self):
        """Region code."""
        return self._region_code

    @property
    def device_ip(self):
        """Ip."""
        network = next(
            (network for network in self._networks if network.type == "SMSC"),
            next((network for network in self._networks), None))
        return network.ip_address if network else None

    @property
    def mac_address(self):
        """Mac address."""
        network = next(
            (network for network in self._networks if network.type == "SMSC"),
            next((network for network in self._networks), None))
        return network.mac_address if network else None


class Network:
    """Soundtouch network configuration."""

    def __init__(self, network_dom):
        """Create a new Network.

        :param network_dom: Network configuration XML DOM
        """
        self._type = network_dom.attributes["type"].value
        self._mac_address = _get_dom_element_value(network_dom, "macAddress")
        self._ip_address = _get_dom_element_value(network_dom, "ipAddress")

    @property
    def type(self):
        """Type."""
        return self._type

    @property
    def mac_address(self):
        """Mac Address."""
        return self._mac_address

    @property
    def ip_address(self):
        """IP Address."""
        return self._ip_address


class Component:
    """Soundtouch component."""

    def __init__(self, component_dom):
        """Create a new Component.

        :param component_dom: Component XML DOM
        """
        self._category = _get_dom_element_value(component_dom,
                                                "componentCategory")
        self._software_version = _get_dom_element_value(component_dom,
                                                        "softwareVersion")
        self._serial_number = _get_dom_element_value(component_dom,
                                                     "serialNumber")

    @property
    def category(self):
        """Category."""
        return self._category

    @property
    def software_version(self):
        """Software version."""
        return self._software_version

    @property
    def serial_number(self):
        """Return serial number."""
        return self._serial_number


class Status:
    """Soundtouch device status."""

    def __init__(self, xml_dom):
        """Create a new device status.

        :param xml_dom: Status XML DOM
        """
        self._source = _get_dom_element_attribute(xml_dom, "nowPlaying",
                                                  "source")
        self._content_item = ContentItem(
            _get_dom_element(xml_dom, "ContentItem"))
        self._track = _get_dom_element_value(xml_dom, "track")
        self._artist = _get_dom_element_value(xml_dom, "artist")
        self._album = _get_dom_element_value(xml_dom, "album")
        image_status = _get_dom_element_attribute(xml_dom, "art",
                                                  "artImageStatus")
        if image_status == "IMAGE_PRESENT":
            self._image = _get_dom_element_value(xml_dom, "art")
        else:
            self._image = None

        duration = _get_dom_element_attribute(xml_dom, "time", "total")
        self._duration = int(duration) if duration is not None else None
        position = _get_dom_element_value(xml_dom, "time")
        self._position = int(position) if position is not None else None
        self._play_status = _get_dom_element_value(xml_dom, "playStatus")
        self._shuffle_setting = _get_dom_element_value(xml_dom,
                                                       "shuffleSetting")
        self._repeat_setting = _get_dom_element_value(xml_dom, "repeatSetting")
        self._stream_type = _get_dom_element_value(xml_dom, "streamType")
        self._track_id = _get_dom_element_value(xml_dom, "trackID")
        self._station_name = _get_dom_element_value(xml_dom, "stationName")
        self._description = _get_dom_element_value(xml_dom, "description")
        self._station_location = _get_dom_element_value(xml_dom,
                                                        "stationLocation")

    @property
    def source(self):
        """Source."""
        return self._source

    @property
    def content_item(self):
        """Content item."""
        return self._content_item

    @property
    def track(self):
        """Track."""
        return self._track

    @property
    def artist(self):
        """Artist."""
        return self._artist

    @property
    def album(self):
        """Album name."""
        return self._album

    @property
    def image(self):
        """Image URL."""
        return self._image

    @property
    def duration(self):
        """Duration."""
        return self._duration

    @property
    def position(self):
        """Position."""
        return self._position

    @property
    def play_status(self):
        """Status."""
        return self._play_status

    @property
    def shuffle_setting(self):
        """Shuffle setting."""
        return self._shuffle_setting

    @property
    def repeat_setting(self):
        """Repeat setting."""
        return self._repeat_setting

    @property
    def stream_type(self):
        """Stream type."""
        return self._stream_type

    @property
    def track_id(self):
        """Track id."""
        return self._track_id

    @property
    def station_name(self):
        """Station name."""
        return self._station_name

    @property
    def description(self):
        """Description."""
        return self._description

    @property
    def station_location(self):
        """Station location."""
        return self._station_location


class ContentItem:
    """Content item."""

    def __init__(self, xml_dom):
        """Create a new content item.

        :param xml_dom: Content item XML DOM
        """
        self._name = _get_dom_element_value(xml_dom, "itemName")
        self._source = _get_dom_attribute(xml_dom, "source")
        self._type = _get_dom_attribute(xml_dom, "type")
        self._location = _get_dom_attribute(xml_dom, "location")
        self._source_account = _get_dom_attribute(xml_dom, "sourceAccount")
        self._is_presetable = _get_dom_attribute(xml_dom,
                                                 "isPresetable") == 'true'

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def source(self):
        """Source."""
        return self._source

    @property
    def type(self):
        """Type."""
        return self._type

    @property
    def location(self):
        """Location."""
        return self._location

    @property
    def source_account(self):
        """Source account."""
        return self._source_account

    @property
    def is_presetable(self):
        """Return true if presetable."""
        return self._is_presetable


class Volume:
    """Volume configuration."""

    def __init__(self, xml_dom):
        """Create a new volume configuration.

        :param xml_dom: Volume configuration XML DOM
        """
        self._actual = int(_get_dom_element_value(xml_dom, "actualvolume"))
        self._target = int(_get_dom_element_value(xml_dom, "targetvolume"))
        self._muted = _get_dom_element_value(xml_dom, "muteenabled") == "true"

    @property
    def actual(self):
        """Actual volume level."""
        return self._actual

    @property
    def target(self):
        """Target volume level."""
        return self._target

    @property
    def muted(self):
        """Return True if volume is muted."""
        return self._muted


class Preset:
    """Preset."""

    def __init__(self, preset_dom):
        """Create a preset configuration.

        :param preset_dom: Preset configuration XML DOM
        """
        self._name = _get_dom_element_value(preset_dom, "itemName")
        self._id = _get_dom_attribute(preset_dom, "id")
        self._source = _get_dom_element_attribute(preset_dom, "ContentItem",
                                                  "source")
        self._type = _get_dom_element_attribute(preset_dom, "ContentItem",
                                                "type")
        self._location = _get_dom_element_attribute(preset_dom, "ContentItem",
                                                    "location")
        self._source_account = _get_dom_element_attribute(preset_dom,
                                                          "ContentItem",
                                                          "sourceAccount")
        self._is_presetable = \
            _get_dom_element_attribute(preset_dom,
                                       "ContentItem",
                                       "isPresetable") == "true"
        self._source_xml = _get_dom_element(preset_dom, "ContentItem").toxml()

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def preset_id(self):
        """Id."""
        return self._id

    @property
    def source(self):
        """Source."""
        return self._source

    @property
    def type(self):
        """Type."""
        return self._type

    @property
    def location(self):
        """Location."""
        return self._location

    @property
    def source_account(self):
        """Source account."""
        return self._source_account

    @property
    def is_presetable(self):
        """Return True if is presetable."""
        return self._is_presetable

    @property
    def source_xml(self):
        """XML source."""
        return self._source_xml


class ZoneStatus:
    """Zone Status."""

    def __init__(self, zone_dom):
        """Create a new Zone status configuration.

        :param zone_dom: Zone status configuration XML DOM
        """
        self._master_id = _get_dom_element_attribute(zone_dom, "zone",
                                                     "master")
        self._master_ip = _get_dom_element_attribute(zone_dom, "zone",
                                                     "senderIPAddress")
        self._is_master = self._master_ip is None
        members = _get_dom_elements(zone_dom, "member")
        self._slaves = []
        for member in members:
            self._slaves.append(ZoneSlave(member))

    @property
    def master_id(self):
        """Master id."""
        return self._master_id

    @property
    def is_master(self):
        """Return True if current device is the zone master."""
        return self._is_master

    @property
    def master_ip(self):
        """Master ip."""
        return self._master_ip

    @property
    def slaves(self):
        """Zone slaves."""
        return self._slaves


class ZoneSlave:
    """Zone Slave."""

    def __init__(self, member_dom):
        """Create a new Zone slave configuration.

        :param member_dom: Slave XML DOM
        """
        self._ip = _get_dom_attribute(member_dom, "ipaddress")
        self._role = _get_dom_attribute(member_dom, "role")

    @property
    def device_ip(self):
        """Slave ip."""
        return self._ip

    @property
    def role(self):
        """Slave role."""
        return self._role


class SoundtouchException(Exception):
    """Parent Soundtouch Exception."""

    def __init__(self):
        """Soundtouch Exception."""
        super(SoundtouchException, self).__init__()


class NoExistingZoneException(SoundtouchException):
    """Exception while trying to add slave(s) without existing zone."""

    def __init__(self):
        """NoExistingZoneException."""
        super(NoExistingZoneException, self).__init__()


class NoSlavesException(SoundtouchException):
    """Exception while managing multi-room actions without valid slaves."""

    def __init__(self):
        """NoSlavesException."""
        super(NoSlavesException, self).__init__()
