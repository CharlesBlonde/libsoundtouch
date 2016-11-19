"""libsoundtouch."""

from libsoundtouch.device import SoundTouchDevice


def soundtouch_device(host, port=8090):
    """Create a new Soundtouch device.

    :param host: Host of the device
    :param port: Port of the device. Default 8090

    """
    s_device = SoundTouchDevice(host, port)
    return s_device
