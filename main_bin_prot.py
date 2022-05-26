import os
import signal
import subprocess
from operator import le
import sys
import time
import pygame
import pygame.display
import pygame.key
import pygame.locals
import pygame.font
import traceback
from subprocess import Popen, PIPE

from TelloPy.tellopy._internal import tello

from input import DSenseTello
from pydualsense import *

import utils


#settings
CONTROL_LOOP_INTERVAL=0.001
STREAMING_CMD="ffplay -probesize 32 -i udp://0.0.0.0:11111 -framerate 30 > /dev/null"

prev_flight_data = None
flight_data = None
video_player = None
video_recorder = None
font = None
wid = None

def handler(event, sender, data, **args):
    global prev_flight_data
    global flight_data
    global log_data
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            print(data)
            prev_flight_data = str(data)
        flight_data = data
    elif event is drone.EVENT_LOG_DATA:
        log_data = data
    else:
        print('event="%s" data=%s' % (event.getname(), str(data)))

def videoFrameHandler(event, sender, data):
    global video_player
    global video_recorder
    if video_player is None:
        cmd = [ 'mplayer', '-fps', '35', '-really-quiet' ]
        if wid is not None:
            cmd = cmd + [ '-wid', str(wid) ]
        video_player = Popen(cmd + ['-'], stdin=PIPE)

    try:
        video_player.stdin.write(data)
    except IOError as err:
        video_player = None

    try:
        if video_recorder:
            video_recorder.stdin.write(data)
    except IOError as err:
        video_recorder = None

def main():
	print('demo started')
	pygame.init()
	pygame.display.init()
	pygame.display.set_mode((1280, 720))
	pygame.font.init()

	global font
	font = pygame.font.SysFont("dejavusansmono", 32)
	global wid
	if 'window' in pygame.display.get_wm_info():
		wid = pygame.display.get_wm_info()['window']
	print("Tello video WID:", wid)	


	# setup dualsense controller
	dsTello=DSenseTello()

	#Tello binary protocol
	global drone
	drone= tello.Tello()
	drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
	drone.subscribe(drone.EVENT_LOG_DATA, handler)
	drone.subscribe(drone.EVENT_VIDEO_FRAME, videoFrameHandler)

	#internal flags
	telloTookOff=False
	streamingOn=False
	try:
		drone.connect()
		drone.wait_for_connection(60.0)
		drone.start_video()
		drone.toggle_fast_mode()
		pygame.init()
		pygame.display.init()
		pygame.display.set_mode((1280, 720))
		pygame.font.init()

		while True:
			#-------# mainloop
			if( dsTello.conditionArm() and not telloTookOff ): # takeoff procedure
				dsTello.onArmed()
				if(dsTello.conditionTakeOff()):
					dsTello.onTakeOff()
					drone.takeoff()
					#-----# post takeoff actions
					telloTookOff=True
					dsTello.onTakeOffDone()

			if(dsTello.condition_throw_and_go()):
				drone.throw_and_go()
				time.sleep(1)
				telloTookOff=True
			elif( dsTello.conditionLand() ): #landing 
				print("land")
				drone.land()
				dsTello.onLandDone()
				telloTookOff=False
				
			elif( telloTookOff ):
				RC_Input=dsTello.getRCInputValues()
				#print("sticks positions: "+"rc "+str(RC_Input[0])+" "+str(RC_Input[1])+" "+str(RC_Input[2])+" "+str(RC_Input[3]))
				#tello.send_command("rc "+str(RC_Input[0])+" "+str(RC_Input[1])+" "+str(RC_Input[2])+" "+str(RC_Input[3]),0)
				drone.set_roll(RC_Input[0]/100)
				drone.set_pitch(RC_Input[1]/100)
				drone.set_throttle(RC_Input[2]/100)
				drone.set_yaw(RC_Input[3]/100)

				dsense = dsTello.getDSene()
				if(dsTello.conditionFlipRight()):
					drone.flip_right()
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipLeft()):
					drone.flip_left()
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipFwd()):
					drone.flip_forward()
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipBwd()):
					drone.flip_back()
					while(dsTello.flipLock()): pass

				if(dsTello.condition_palm_land()):
					drone.palm_land()

				if(dsTello.condition_demo()):
					demo_sequence()
					
			else:	# all buttons released
				if(not telloTookOff):
					dsTello.onGroundAndNoInput()

			#------# actions possible when connection is up #-------#
			if(bool(drone.connected and flight_data is not None)): # if is connected
				dsTello.batteryLevelIndicator(flight_data.battery_percentage)
				if(telloTookOff):
					dsTello.adaptTriggerInFlight(flight_data.battery_percentage)
				if(dsTello.dsense.state.share):
					if(not streamingOn): #enable streaming if not already enabled
						print("Start video")
						#drone.start_video()
						streamingOn = True
						time.sleep(0.3)
					else: #disable streaming if currently enabled 
						streamingOn = False
						time.sleep(0.2)

					
			time.sleep(CONTROL_LOOP_INTERVAL)
			#-------# mainloop end

	except KeyboardInterrupt:
		print('\ninterrupted, closing connections...')
		drone.quit()
#-----------### main end ###--------#


def demo_sequence():
	drone.flip_forward()
	time.sleep(2.2)
	drone.flip_back()
	time.sleep(2.2)
	

		
if __name__ == "__main__": main()
