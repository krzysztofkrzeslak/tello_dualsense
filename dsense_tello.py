from pydualsense import pydualsense
from pydualsense.enums import *
from time import sleep
import utils

R_JOYSTICK_XY_RC_RANGE = 100     #range should be 0-100
L_JOYSTICK_XY_RC_RANGE = 55     #range should be 0-100
R1L1_TRG_YAW_RC_RANGE   = 100    #range should be 0-100
R2L2_TRG_UP_DN_RC_RANGE = 100    #range should be 0-100

class DSenseTello:
    def __init__(self):
        self.dsense = pydualsense()
        self.dsense.init() 
        self.dsense.light.setLEDOption(LedOptions.Both)
        self.dsense.light.setPulseOption(PulseOptions.FadeOut)
        self.dsense.light.setPlayerID(PlayerID.player1)
        self.dsense.light.setBrightness(Brightness.high)
        self.dsense.light.setColorI(255,0,0)
        self.dsense.state.LX = 0
        self.dsense.state.LY = 0
    
    def getDSene(self):
        return self.dsense

    def conditionArm(self):
        return (self.dsense.state.triangle and self.dsense.state.L1)

    def onArmed(self):
        print("armed!!! ready to take off", sep=' ', end='\r', flush=True)
        self.dsense.triggerR.setMode(TriggerModes.Pulse)
        self.dsense.triggerR.setForce(0, 30)
        self.dsense.triggerR.setForce(1, 180)
        self.dsense.light.setColorI(0,255,0)

    def conditionTakeOff(self):
        return (self.dsense.state.R2 == 255)
    
    def onTakeOff(self):
        self.dsense.triggerR.setForce(0, 0)
        self.dsense.setBothMotors(30)

    def onTakeOffDone(self):
        self.dsense.setBothMotors(0)
        self.dsense.triggerR.setForce(0, 255)
        while(self.dsense.state.R2 > 0 or self.dsense.state.triangle or self.dsense.state.L1 ): pass #lock any action until take off combination released
        self.dsense.triggerL.setMode(TriggerModes.Rigid)
        self.dsense.triggerR.setMode(TriggerModes.Rigid)

    def conditionLand(self):
        return (self.dsense.state.triangle and not self.dsense.state.L1 and not self.dsense.state.L3)
    
    def onLandDone(self):
        self.dsense.setBothMotors(80)
        sleep(0.3)
        self.dsense.setBothMotors(0)
        while(self.dsense.state.triangle): pass #lock until released

    def getRCInputValues(self):
        #Read Left Joystick
        L_leftRightRCValue=utils.translate(self.dsense.state.LX, -128,128,-L_JOYSTICK_XY_RC_RANGE,L_JOYSTICK_XY_RC_RANGE)
        L_fwdBwdRCValue=(utils.translate(self.dsense.state.LY*(-1), -128,128,-L_JOYSTICK_XY_RC_RANGE,L_JOYSTICK_XY_RC_RANGE))
        if(abs(L_leftRightRCValue)<5): L_leftRightRCValue = 0
        if(abs(L_fwdBwdRCValue)<5): L_fwdBwdRCValue = 0
        #Read Right JoyStick
        R_leftRightRCValue=utils.translate(self.dsense.state.RX, -128,128,-R_JOYSTICK_XY_RC_RANGE,R_JOYSTICK_XY_RC_RANGE)
        R_fwdBwdRCValue=(utils.translate(self.dsense.state.RY*(-1), -128,128,-R_JOYSTICK_XY_RC_RANGE,R_JOYSTICK_XY_RC_RANGE))
        if(abs(R_leftRightRCValue)<5): R_leftRightRCValue = 0
        if(abs(R_fwdBwdRCValue)<5): R_fwdBwdRCValue = 0
        # Sum input from both joysticks
        leftRightRCValue=L_leftRightRCValue+R_leftRightRCValue
        fwdBwdRCValue = L_fwdBwdRCValue + R_fwdBwdRCValue
        if(leftRightRCValue) > 100: leftRightRCValue = 100
        if(fwdBwdRCValue) > 100 : fwdBwdRCValue = 100
        #Read Triggers
        upDwnRCValue= utils.translate( (self.dsense.state.R2 - self.dsense.state.L2), -255,255, -R2L2_TRG_UP_DN_RC_RANGE, R2L2_TRG_UP_DN_RC_RANGE )
        if(self.dsense.state.L1): yawRCValue   = -R1L1_TRG_YAW_RC_RANGE
        elif(self.dsense.state.R1): yawRCValue = R1L1_TRG_YAW_RC_RANGE
        else: yawRCValue = 0

        return [leftRightRCValue, fwdBwdRCValue, upDwnRCValue, yawRCValue]

    def conditionFlipRight(self):
        return (self.dsense.state.L3 and self.dsense.state.circle)
    
    def conditionFlipLeft(self):
        return (self.dsense.state.L3 and self.dsense.state.square)
    
    def conditionFlipFwd(self):
        return (self.dsense.state.L3 and self.dsense.state.triangle)

    def conditionFlipBwd(self):
        return (self.dsense.state.L3 and self.dsense.state.cross)

    def flipLock(self):
        return self.dsense.state.L3

    def onGroundAndNoInput(self):
        self.dsense.light.setColorI(255,0,0)

    def batteryLevelIndicator(self, batteryLevel):
        if(batteryLevel > 80): self.dsense.light.setPlayerID(PlayerID.player4)
        elif(batteryLevel > 60): self.dsense.light.setPlayerID(PlayerID.player3)
        elif(batteryLevel > 35 ): self.dsense.light.setPlayerID(PlayerID.player2)
        elif(batteryLevel > 20 ): self.dsense.light.setPlayerID(PlayerID.player1)
        else: self.dsense.audio.microphone_led = True

    def adaptTriggerInFlight(self, battery):
        trgForcePoint = utils.translate(battery, 0, 100, 0, 120)
        trgForce = utils.translate(battery, 0, 100, 120, 0)  
        self.dsense.triggerR.setForce(0, trgForcePoint)
        self.dsense.triggerR.setForce(1, trgForce)
        self.dsense.triggerL.setForce(0, trgForcePoint)
        self.dsense.triggerL.setForce(1, trgForce)
        print("baterry: "+str(battery)+" force: "+str(trgForce)+" Force point: "+str(trgForcePoint))

    def close(self):
        self.dsense.light.setColorI(0,0,255)
        self.dsense.light.setBrightness(Brightness.low)
        self.dsense.light.setPlayerID(PlayerID.player1)
        self.dsense.triggerR.setMode(TriggerModes.Rigid)
        self.dsense.triggerR.setForce(1, 0)
        self.dsense.triggerL.setForce(1, 0)
        sleep(1)
        self.dsense.close()
