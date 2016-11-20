# Bose Soundtouch Python library

[![Build Status](https://travis-ci.org/CharlesBlonde/libsoundtouch.svg?branch=master)](https://travis-ci.org/CharlesBlonde/libsoundtouch) [![Coverage Status](https://coveralls.io/repos/github/CharlesBlonde/libsoundtouch/badge.svg?branch=master)](https://coveralls.io/github/CharlesBlonde/libsoundtouch?branch=master)

This Python library allows you to control [Bose Soundtouch devices](https://www.soundtouch.com/).

## How to use it ?

```shell
pip install libsoundtouch
```

```python
from libsoundtouch import soundtouch_device

device = soundtouch_device('192.168.18.118')
device.power_on()
status = device.status()
print(status.source)
print(status.artist+ " - "+ status.track)
device.pause()
device.next_track()
device.play()
```
