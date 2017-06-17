.. _api:

Developer Interface
===================

.. module:: libsoundtouch

This part of the documentation covers all the interfaces of Libsoundtouch.

Main Interface
--------------

.. autofunction:: soundtouch_device
.. autofunction:: discover_devices

Classes
-------

.. automodule:: libsoundtouch.device

.. autoclass:: SoundTouchDevice
    :members:

.. autoclass:: Config
    :members:

.. autoclass:: Network
    :members:

.. autoclass:: Component
    :members:

.. autoclass:: Status
    :members:

.. autoclass:: ContentItem
    :members:

.. autoclass:: Volume
    :members:

.. autoclass:: Preset
    :members:

.. autoclass:: ZoneStatus
    :members:

.. autoclass:: ZoneSlave
    :members:

Exceptions
----------

.. autoexception:: SoundtouchException
.. autoexception:: NoExistingZoneException
.. autoexception:: NoSlavesException
