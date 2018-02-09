from __future__ import print_function
from libsoundtouch import soundtouch_device
from libsoundtouch.device import get_source_type
from libsoundtouch.utils import Source, Type, Key, SourceStatus
from cmd import Cmd
from requests.exceptions import ConnectionError
import sys
import logging
from pprint import pprint

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)

class SoundtouchPrompt(Cmd):

	def __init__(self,device):
		Cmd.__init__(self)
		self._device = device
		self._device.add_volume_listener(volume_listener)
		self._device.add_status_listener(status_listener)
		self._device.add_presets_listener(preset_listener)
		self._device.add_zone_status_listener(zone_status_listener)
		# Start websocket thread. Not started by default
		self._device.start_notification()

	def do_status(self, args):
		"""Requests and prints the device's status"""
		status = self._device.status()
		print_status(status)

	def do_sources_get(self,args):
		"""Get availabe sources"""
		sources = self._device.sources()
		i = 0
		for source in sources:
			print('Id: ' + str(i) + ', Name: "' + str(source.name), end='')
			print('", Status: ' + source.status, end='')
			print(', Source: ' + get_source_type(source), end='')
			print(', Local: ' + str(source.local), end='')
			print(', Source Account: "' + str(source.source_account) + '"')
			i = i + 1

	def do_sources_show(self,value):
		"""Show content of a specific source"""
		if len(value) == 0:
			print('Please provide an index.')
			return
		try:
			idx = int(value)
		except ValueError:
			print('Source has to an integer to base 10')
			return
		sources = self._device.sources()
		if idx < 0 or idx > len(sources):
			print('Index has to be between 0 and ' + len(sources))
			return
		print(sources[idx].name)
		items = self._device.get_source_content(idx)
		i = 0
		for item in items:
			print('Id: ' + str(i) + ', Name: "' + str(item.name) + '"')
			i = i + 1

	def do_mute(self, args):
		"""Mute/Un-mute volume."""
		self._device.mute()

	def do_vol_get(self, args):
		"""Get current volume."""
		print('Volume: ' + str(self._device.volume().actual))

	def do_vol_set(self, value):
		"""Vol_set [value].
			Sets current volume"""
		if len(value) == 0:
			print('Please provide a volume level.')
			return
		try:
			volume = int(value)
		except ValueError:
			print('Target volume has to an integer to base 10')
			return
		if volume < 0 or volume > 100:
			print('Volume has to be between 0 and 100')
			return
		self._device.set_volume(volume)

	def do_preset_get(self,value):
		"""Preset_get
			Retrieves all presets from device, and prints them"""
		presets = self._device.presets()
		for preset in presets:
			print('ID: ' + preset.preset_id + ', Name: "' + preset.name + '"')
			#pprint(vars(preset))

	def do_preset_play(self,value):
		"""Preset_play [preset number]"""
		if len(value) == 0:
			print('Please provide a preset.')
			return
		try:
			presetIdx = int(value)
		except ValueError:
			print('Preset has to an integer to base 10')
			return
		if presetIdx < 1 or presetIdx > 6:
			print('Volume has to be between 1 and 6')
			return
		presets = self._device.presets()
		self._device.select_preset(presets[presetIdx - 1])

	def do_vol_up(self, args):
		"""Volume up."""
		self._device.volume_up()

	def do_vol_down(self, args):
		"""Volume down."""
		self._device.volume_down()

	def do_next(self, args):
		"""Switch to next track."""
		self._device.next_track()

	def do_prev(self, args):
		"""Switch to previous track."""
		self._device.previous_track()

	def do_pause(self, args):
		"""Pause."""
		self._device.pause()

	def do_play(self, args):
		"""Play."""
		self._device.play()

	def do_play_pause(self, args):
		"""Toggle play status."""
		self._device.play_pause()

	def do_play_url(self,url):
		"""Play_url [url]"""
		if len(url) == 0:
			print('Please provide an URL')
			return
		self._device.play_url(url)

	def do_repeat_off(self, args):
		"""Turn off repeat."""
		self._device.repeat_off()

	def do_repeat_one(self, args):
		"""Repeat one."""
		self._device.repeat_one()

	def do_repeat_all(self, args):
		"""Repeat all."""
		self._device.repeat_all()

	def do_shuffle(self, shuffle):
		"""Shuffle [on/off].
		:param shuffle: Boolean on/off
		"""
		if len(shuffle) == 0:
			print('Please provide a status')
			return
		if shuffle.lower() == 'on':
			print('Turning shuffle mode on')
			self._device.shuffle(True)
		elif shuffle.lower() == 'off':
			print('Turning shuffle mode off')
			self._device.shuffle(False)
		else:
			print('Unkown shuffle mode')

	def do_poweroff(self, args):
		"""Turn the device off"""
		self._device.power_off()

	def do_poweron(self, args):
		"""Turn the device on"""
		self._device.power_on()

	def do_quit(self, args):
		"""Quits the program."""
		self._device.stop_notification()
		print("Quitting.")
		raise SystemExit

	def do_EOF(self,line):
		self._device.stop_notification()
		return True

def print_status(status):
	pprint(vars(status))
	pprint(vars(status.content_item))
	if status.source == Source.INTERNET_RADIO.name:
		print('Source: Internet Radio')
		if status.station_name is not None:
			print('Station: ' + status.station_name + ' from ' + status.station_location)
			print('Description: "' + status.description + '"')
		print_play_status(status.play_status)
	elif status.source == Source.STORED_MUSIC.name:
		print('Source: Stored Music')
		print('Artist - Title: "' + status.artist + '" - "' + status.track + '"')
		print('Album: "' + status.album + '"')
		print_play_status(status.play_status, eol='')
		print(' @ ' + str(status.position) + '/' + str(status.duration) + ', Shuffle: ', end='')
		if status.shuffle_setting == Key.SHUFFLE_OFF.name:
			print('off', end='')
		elif status.shuffle_setting == Key.SHUFFLE_ON.name:
			print('on', end='')
		print(', Repeat: ', end='')
		if status.repeat_setting == Key.REPEAT_OFF.name:
			print('off')
		elif status.repeat_setting == Key.REPEAT_ONE.name:
			print('one')
		elif status.repeat_setting == Key.REPEAT_ALL.name:
			print('all')
	elif status.source == Source.AUX.name:
		print('Source: Aux')
	elif status.source == Source.BLUETOOTH.name:
		print('Source: Bluetooth')
		if status.play_status == 'INVALID_PLAY_STATUS':
			return
		print('Device: ' + status.station_name)
		if status.artist != None:
			print('Artist - Title: "' + status.artist + '" - "' + status.track + '"')
			print('Album: "' + status.album + '"')
		print_play_status(status.play_status)
	elif status.source == Source.STANDBY.name:
		print('The device is currently in standby.')
	elif status.source == Source.UPNP.name:
		print('Source: UPNP')
		if status.stream_type == 'TRACK_ONDEMAND':
			print('Location: ' + status.content_item.location)
		print_play_status(status.play_status)
	else:
		pprint(vars(status))
		pprint(vars(status.content_item))

def print_play_status(status, eol='\n'):
	print('Status: ', end='')
	if status == 'PLAY_STATE' :
		print('Playing', end=eol)
	elif status == 'PAUSE_STATE' :
		print('Paused', end=eol)
	elif status == 'STOP_STATE':
		print('Stopped', end=eol)
	elif status == 'BUFFERING_STATE':
		print('Loading', end=eol)
	else:
		print('Unkown', end=eol)

# Volume updated
def volume_listener(volume):
	print('WebSocket - Volume: ' + int(volume.actual))

# Status updated
def status_listener(status):
	print('WebSocket - Status: ')
	print_status(status)

# Presets updated
def preset_listener(presets):#
	print('WebSocket - Presets: ')
	for preset in presets:
		print(preset.name)

# Zone updated
def zone_status_listener(zone_status):
	if zone_status:
		print(zone_status.master_id)
	else:
		print('no Zone')

if __name__ == '__main__':
	global device

	if len(sys.argv) > 1:
		host = sys.argv[1]
	else:
		host = '192.168.111.106'
	try:
		device = soundtouch_device(host)
	except ConnectionError as e:
		print('Could not connect to device(' + host + '):\n' + e.__str__() + '\n', file=sys.stderr)
		exit(-1)

	# Config object
	print('Connected to \'' + device.config.name + '(@ ' + host + ')\'')
	prompt = SoundtouchPrompt(device)
	prompt.prompt = '> '
	prompt.cmdloop('Starting prompt...')
