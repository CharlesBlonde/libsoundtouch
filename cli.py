from __future__ import print_function
from libsoundtouch import soundtouch_device
from libsoundtouch.utils import Source, Type, Key
from cmd import Cmd
from requests.exceptions import ConnectionError
import sys
import logging
from pprint import pprint


class SoundtouchPrompt(Cmd):

	def __init__(self,device):
		Cmd.__init__(self)
		self._device = device

	def do_status(self, args):
		"""Requests and prints the device's status"""
		status = device.status()
		if status.source == Source.INTERNET_RADIO.name:
			print('Source: Internet Radio')
			print('Station: ' + status.station_name + ' from ' + status.station_location)
			print('Status: ', end='')
			if status.play_status == 'PLAY_STATE' :
				print('Playing')
			else:
				print('Stopped')
			print('Description: "' + status.description + '"')
		elif status.source == Source.STORED_MUSIC.name:
			print('Source: Stored Music')
			print('Artist - Title: "' + status.artist + '" - "' + status.track + '"')
			print('Album: "' + status.album + '"')
			print('Status: ', end='')
			if status.play_status == 'PLAY_STATE' :
				print('Playing', end='')
			elif status.play_status == 'PAUSE_STATE' :
				print('Paused', end='')
			elif status.play_status == 'STOP_STATE':
				print('Stopped', end='')
			else:
				print('Unkown', end='')
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
			print('Status: ', end='')
			if status.play_status == 'PLAY_STATE' :
				print('Playing')
			elif status.play_status == 'PAUSE_STATE' :
				print('Paused')
			elif status.play_status == 'STOP_STATE':
				print('Stopped')
			else:
				print('Unkown')
		elif status.source == Source.STANDBY.name:
			print('The device is currently in standby.')
		else:
			pprint(vars(status))

	def do_mute(self, args):
		"""Mute/Un-mute volume."""
		device.mute()

	def do_volup(self, args):
		"""Volume up."""
		device.volume_up()

	def do_voldown(self, args):
		"""Volume down."""
		device.volume_down()

	def do_next(self, args):
		"""Switch to next track."""
		device.next_track()

	def do_prev(self, args):
		"""Switch to previous track."""
		device.previous_track()

	def do_pause(self, args):
		"""Pause."""
		device.pause()

	def do_play(self, args):
		"""Play."""
		device.play()

	def do_play_pause(self, args):
		"""Toggle play status."""
		device.play_pause()

	def do_repeat_off(self, args):
		"""Turn off repeat."""
		device.repeat_off()

	def do_repeat_one(self, args):
		"""Repeat one."""
		device.repeat_one()

	def do_repeat_all(self, args):
		"""Repeat all."""
		device.repeat_all()

	def do_shuffle(self, shuffle):
		"""Shuffle [on/off].
		:param shuffle: Boolean on/off
		"""
		if len(shuffle) == 0:
			print('Please provide a status')
			return
		if shuffle.lower() == 'on':
			print('Turning shuffle mode on')
			device.shuffle(True)
		elif shuffle.lower() == 'off':
			print('Turning shuffle mode off')
			device.shuffle(False)
		else:
			print('Unkown shuffle mode')

	def do_poweroff(self, args):
		"""Turn the device off"""
		device.power_off()

	def do_poweron(self, args):
		"""Turn the device on"""
		device.power_on()

	def do_quit(self, args):
		"""Quits the program."""
		print("Quitting.")
		raise SystemExit



if __name__ == '__main__':
	global device

	if len(sys.argv) > 1:
		host = sys.argv[1]
	else:
		host = '192.168.111.106'
	try:
		device = soundtouch_device(host)
		device.power_on()
	except ConnectionError as e:
		print('Could not connect to device(' + host + '):\n' + e.__str__() + '\n', file=sys.stderr)
		exit(-1)

	# Config object
	print('Connected to \'' + device.config.name + '(@ ' + host + ')\'')
	prompt = SoundtouchPrompt(device)
	prompt.prompt = '> '
	prompt.cmdloop('Starting prompt...')
