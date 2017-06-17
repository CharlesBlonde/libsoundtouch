"""libsoundtouch."""

import logging

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # type: ignore
from libsoundtouch.device import SoundTouchDevice
from libsoundtouch.utils import SoundtouchDeviceListener
from zeroconf import Zeroconf, ServiceBrowser

_LOGGER = logging.getLogger(__name__)


def soundtouch_device(host, port=8090):
    """Create a new Soundtouch device.

    :param host: Host of the device
    :param port: Port of the device. Default 8090

    """
    s_device = SoundTouchDevice(host, port)
    return s_device


def discover_devices(timeout=5):
    """Discover devices on the local network.

    :param timeout: Max time to wait in seconds. Default 5
    """
    devices = []
    # Using Queue as a timeout timer
    add_devices_queue = Queue()

    def add_device_function(name, host, port):
        """Add device callback."""
        _LOGGER.info("%s discovered (host: %s, port: %i)", name, host, port)
        devices.append(soundtouch_device(host, port))

    zeroconf = Zeroconf()
    listener = SoundtouchDeviceListener(add_device_function)
    _LOGGER.debug("Starting discovery...")
    ServiceBrowser(zeroconf, "_soundtouch._tcp.local.", listener)
    try:
        add_devices_queue.get(timeout=timeout)
    except Empty:
        _LOGGER.debug("End of discovery...")
    return devices
