import sys
import time
import pyactr
# from XPlaneConnect import *
import xpc
import math
# import geopy
from geographiclib.geodesic import Geodesic as geo
from rich import print
from sandbox import sandbox as sb
from modelParameters import params
# import scaleFactor as sf
# Initialize XPlaneConnect client
from modelParameters import *

### Define variables/parameters for aircraft class/category : Wisdom of Raju 
class AircraftLandingModel(pyactr.ACTRModel):
    # TODO: remove pyactr dependency
    

    def __init__(self,client,printFlag):
        super().__init__()
        self.client = client
        self.parameters = params()
        self.parameters.initialize()
        self.inProgress = True
        self.allowPrinting = printFlag
        self.coordinateArray = [[39.896139,-104.689779],[39.875027,-104.696482],[39.903662,-104.695983],[39.901754,-104.715951]]

    def reassignClient(self,newClient):
        self.client = newClient

    def getSimulationStatus(self):
        return self.inProgress

    def get_bearing(self,lat1, lat2, long1, long2): 
        brngAzi = geo.WGS84.Inverse(lat1, long1, lat2, long2)['azi1']
        # print(brng)
        brng = (brngAzi + 360) % 360
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"heading"],listAccess.TARGET.value,permissions.WRITE.value,brng)

    def distanceFromPoint(self,lat1, lat2, long1, long2):
        dist = geo.WGS84.Inverse(lat1, long1, lat2, long2)['s12']
        print(dist)
        return dist


    def getAndLoadDREFS(self):
        try:
            sources = self.parameters.getModelDREFS()
            keys =  self.parameters.getModelKeys()
            results = self.client.getDREFs(sources)
            # idx = 0
            keyValueResults = list(zip(keys,results))
            # print(keyValueResults)

            for (key,value) in keyValueResults:
                self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,key],listAccess.CURRENT.value,permissions.WRITE.value,value[0])

            lat  = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"latitude"],listAccess.CURRENT.value,permissions.READ)
            long = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"longitude"],listAccess.CURRENT.value,permissions.READ)
            targetLatitude = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"latitude"],listAccess.TARGET.value,permissions.READ)
            targetLongitude = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"longitude"],listAccess.TARGET.value,permissions.READ)
            self.get_bearing(lat,targetLatitude,long,targetLongitude)
            self.parameters.visionCycle() ## Update the vision queue before the next state update
        except Exception as e:
            print(e)

    def proportionalIntegralControl(self,k, delta_theta, k_i,theta,delta_t,deadBand:int = 0): # Edited to match Embry Riddle Equations
        delta_control = 0
        THETA_DEADBAND = deadBand
        # delta_control = k*delta_theta + k_i*theta*delta_t 

        if(theta > THETA_DEADBAND or theta < -THETA_DEADBAND): # Deadband of 0 degrees
            theta_dot = delta_theta / delta_t # TEST for dampening
            delta_control = k*delta_theta + k_i*theta*delta_t - 0.01 * theta_dot

        return delta_control
    
        
    def clamp(self,value,minVal:int=-1,maxVal:int=1):
            return min(maxVal,max(minVal,value))

    def headingToRoll(self,headingDifference):
        rollDegreesTarget = self.clamp(headingDifference/90,-1,1) * 30
        return (rollDegreesTarget)

    
    def update_controls_simultaneously(self):
        """
        Update all controls at the same time by calculating control values for each parameter.
        """
        TESTSCALINGFACTOR = 1
        delta_yoke_pull = self.proportionalIntegralControl(
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.K],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"pitch"],listAccess.DELTA_THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.Ki],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"pitch"],listAccess.THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.TIMING,timeValues.DELTA_T],listAccess.TIMING.value,permissions.READ)
            )
        
        # if(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"pitch"],listAccess.DELTA_THETA.value,permissions.READ) >= 0.05 or 
        #    self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"pitch"],listAccess.DELTA_THETA.value,permissions.READ) <= -0.05):
        #     delta_yoke_pull=0

        ##HEADING
        headingTarget = abs(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"heading"],listAccess.TARGET.value,permissions.READ))
        headingCurrent = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"heading"],listAccess.CURRENT.value,permissions.READ)
        headingDiff = headingTarget - headingCurrent

# 180
# 270

# 270-180 = 90 (Positive = Right Turn)
# 180 - 270 = -90 (Negative, Left Turn)
        rollTarget = self.headingToRoll(headingDiff)
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"roll"],listAccess.TARGET.value,permissions.WRITE.value,rollTarget)\
        
        ##DISTANCE AND LAT LONG TURNOVER
        lat  = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"latitude"],listAccess.CURRENT.value,permissions.READ)
        long = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"longitude"],listAccess.CURRENT.value,permissions.READ)
        targetLatitude = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"latitude"],listAccess.TARGET.value,permissions.READ)
        targetLongitude = self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"longitude"],listAccess.TARGET.value,permissions.READ)
        distance = self.distanceFromPoint(lat,targetLatitude,long,targetLongitude)
        if(distance < 1000):
            print("Coordinates Advancing")
            coordinates = self.coordinateArray.pop()
            print(self.coordinateArray)
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"latitude"],listAccess.TARGET.value,permissions.WRITE.value,coordinates[0])
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"longitude"],listAccess.TARGET.value,permissions.WRITE.value,coordinates[1])
            print(self.coordinateArray)
        

        delta_yoke_steer = self.proportionalIntegralControl(
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.K],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"roll"],listAccess.DELTA_THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.Ki],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"roll"],listAccess.THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.TIMING,timeValues.DELTA_T],listAccess.TIMING.value,permissions.READ)
        )
        
        # if(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"roll"],listAccess.CURRENT.value,permissions.READ) >= 0.1 or 
        #    self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"roll"],listAccess.CURRENT.value,permissions.READ) <= -0.1):
        #     delta_yoke_steer=0

        delta_rudder   = self.proportionalIntegralControl(
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.K],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"slip_skid"],listAccess.DELTA_THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.Ki],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"slip_skid"],listAccess.THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.TIMING,timeValues.DELTA_T],listAccess.TIMING.value,permissions.READ)
        )

        delta_throttle   = self.proportionalIntegralControl(
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.K],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"vertical_speed"],listAccess.DELTA_THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.INTEGRAL_VALUES,integralValues.Ki],listAccess.INTEGRAL_VALUE.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"vertical_speed"],listAccess.THETA.value,permissions.READ),
            self.parameters.dictionaryAccess([parameterType.TIMING,timeValues.DELTA_T],listAccess.TIMING.value,permissions.READ),
            100
        )        
        
        new_yoke_pull   = self.clamp(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.YOKE_PULL],listAccess.CONTROL_VALUE.value,permissions.READ) + delta_yoke_pull)
        new_yoke_steer  = self.clamp(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.YOKE_STEER],listAccess.CONTROL_VALUE.value,permissions.READ) + delta_yoke_steer)
        new_rudder      = self.clamp(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.RUDDER],listAccess.CONTROL_VALUE.value,permissions.READ) + delta_rudder)
        new_throttle    = self.clamp(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.THROTTLE],listAccess.CONTROL_VALUE.value,permissions.READ) + delta_throttle,0)
        
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.YOKE_PULL],listAccess.CONTROL_VALUE.value,permissions.WRITE.value,new_yoke_pull)
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.YOKE_STEER],listAccess.CONTROL_VALUE.value,permissions.WRITE.value,new_yoke_steer)
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.RUDDER],listAccess.CONTROL_VALUE.value,permissions.WRITE.value,new_rudder)
        self.parameters.dictionaryAccess([parameterType.AIRCRAFT_CONTROLS,aircraftControls.THROTTLE],listAccess.CONTROL_VALUE.value,permissions.WRITE.value,new_throttle)


        # start = time.time()
        self.parameters.printParameter(self.allowPrinting)
        # end = time.time()
        # elapsed = end - start
        # print(f"Parameter Print Time: {elapsed} seconds")
        self.send_controls_to_xplane(new_yoke_pull/TESTSCALINGFACTOR,new_yoke_steer/TESTSCALINGFACTOR,  new_rudder/TESTSCALINGFACTOR, new_throttle)

## Pitch at Time, Pitch at Last Cycle, Target Pitch
## Target Pitch - Pitch at Last Cycle = Theta
## Target Pitch - Pitch at Time = CurrTheta
## Theta - CurrTheta = Delta Theta

    def send_controls_to_xplane(self, yoke_pull, yoke_steer, rudder, throttle):
        """
        Sends all control inputs to X-Plane using XPlaneConnect
        """
        self.client.sendCTRL([yoke_pull, yoke_steer, rudder, throttle, -998, -998])  # Control inputs: [yoke_pull, yoke_steer, rudder, throttle]

    def conditionChecks(self):
        flaps = [0]

        if (self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) <= 500):
            # self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"flaps"],listAccess.TARGET.value,permissions.WRITE.value, 0.5)
            flaps = [0]
            if (self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) <= 500):
                flaps = [0.25]
            if (self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) <= 250):
                flaps = [0.55]
            if (self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) <= 100):
                flaps = [1.0]
           
        self.client.sendDREF("sim/flightmodel/controls/flaprqst", flaps)
        if(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"wheelWeight"],listAccess.CURRENT.value,permissions.READ.value) > 0.01
           and self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"wheelSpeed"],listAccess.CURRENT.value,permissions.READ.value) > 1):
            self.parameters.dictionaryAccess([parameterType.PHASE_FLAGS,flightPhase.ROLLOUT.value],listAccess.PHASE_FLAG.value,permissions.WRITE.value, True)
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"brakes"],listAccess.TARGET.value,permissions.WRITE.value, 1)

        if (self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) <= 30 
            and self.parameters.dictionaryAccess([parameterType.PHASE_FLAGS,flightPhase.FLARE.value],listAccess.PHASE_FLAG.value,permissions.READ.value) == False): 
            self.parameters.dictionaryAccess([parameterType.PHASE_FLAGS,flightPhase.FLARE.value],listAccess.PHASE_FLAG.value,permissions.WRITE.value, True)
            self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"pitch"],listAccess.TARGET.value,permissions.WRITE.value, 35)
        else: 
            if(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"altitude"],listAccess.CURRENT.value,permissions.READ.value) >= 30):
                self.parameters.dictionaryAccess([parameterType.PHASE_FLAGS,flightPhase.FLARE.value],listAccess.PHASE_FLAG.value,permissions.WRITE.value, False)



        if(self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"wheelWeight"],listAccess.CURRENT.value,permissions.READ.value) > 0.01 
           and self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"wheelSpeed"],listAccess.CURRENT.value,permissions.READ.value) < 1 
           and self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"airspeed"],listAccess.CURRENT.value,permissions.READ.value) < 2 
           and self.parameters.dictionaryAccess([parameterType.AIRCRAFT_STATE,"brakes"],listAccess.CURRENT.value,permissions.READ.value) == 1):  
            self.inProgress = False

    # Update the model's DM based on X-Plane data
    def update_aircraft_state(self):
        """
        Faster Method
        """
        self.getAndLoadDREFS()
        self.conditionChecks()