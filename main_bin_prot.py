import os
import signal
import subprocess
from operator import le
from sys import stdout
from time import sleep
try:
	from subprocess import DEVNULL # py3k
except ImportError:
	import os
	DEVNULL = open(os.devnull, 'wb')

from dsense_tello import DSenseTello
from pydualsense import *

from tello.tello import Tello
import utils


#settings
CONTROL_LOOP_INTERVAL=0.005
STREAMING_CMD="ffplay -probesize 32 -i udp://0.0.0.0:11111 -framerate 30 > /dev/null"

def main():
	print('demo started')
	# setup dualsense controller
	dsTello=DSenseTello()
	#Tello
	tello = Tello()
	telloTookOff=False
	streamingOn=False
	try:
		tello.send_command("command")
  
		while True:
			#-------# mainloop
			if( dsTello.conditionArm() and not telloTookOff ): # takeoff procedure
				dsTello.onArmed()
				if(dsTello.conditionTakeOff()):
					dsTello.onTakeOff()
					tello.send_command("takeoff")
					#-----# post takeoff actions
					telloTookOff=True
					dsTello.onTakeOffDone()

			elif( dsTello.conditionLand() ): #landing 
				print("land")
				tello.send_command("rc 0 0 0 0", 0)
				tello.send_command("land")
				dsTello.onLandDone()
				telloTookOff=False
				
			elif( telloTookOff ):
				RC_Input=dsTello.getRCInputValues()
				#print("will send rc cmd: "+"rc "+str(RC_Input[0])+" "+str(RC_Input[1])+" "+str(RC_Input[2])+" "+str(RC_Input[3]))
				tello.send_command("rc "+str(RC_Input[0])+" "+str(RC_Input[1])+" "+str(RC_Input[2])+" "+str(RC_Input[3]),0)

				dsense = dsTello.getDSene()
				if(dsTello.conditionFlipRight()):
					tello.send_command("flip r")
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipLeft()):
					tello.send_command("flip l")
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipFwd()):
					tello.send_command("flip f")
					while(dsTello.flipLock()): pass

				if(dsTello.conditionFlipBwd()):
					tello.send_command("flip b")
					while(dsTello.flipLock()): pass

				if(dsense.state.DpadLeft):
					tello.send_command("speed 100")
					tello.send_command("ccw 90")
				if(dsense.state.DpadRight):
					tello.send_command("speed 100")
					tello.send_command("cw 90")
			else:	# all buttons released
				if(not telloTookOff):
					dsTello.onGroundAndNoInput()

			#------# actions possible when connection is up #-------#
			if(bool(tello.status)): # if is connected
				dsTello.batteryLevelIndicator(tello.status["bat"])
				if(telloTookOff):
					dsTello.adaptTriggerInFlight(tello.status["bat"])
				if(dsTello.dsense.state.share):
					if(not streamingOn): #enable streaming is not already enabled
						tello.send_command("streamon")
						pro = subprocess.Popen(STREAMING_CMD, stdout=DEVNULL, stderr=DEVNULL ,shell=True, preexec_fn=os.setsid) 
						streamingOn = True
						sleep(0.3)
					else: #disable streaming if currently enabled
						tello.send_command("streamoff")
						os.killpg(os.getpgid(pro.pid), signal.SIGTERM) 
						streamingOn = False
						sleep(0.2)

					
			sleep(CONTROL_LOOP_INTERVAL)
			#-------# mainloop end

	except KeyboardInterrupt:
		print('\ninterrupted, closing connections...')
		dsTello.close()
		tello.close
		os.killpg(os.getpgid(pro.pid), signal.SIGKILL)
#-----------### main end ###--------#
		
if __name__ == "__main__": main()
