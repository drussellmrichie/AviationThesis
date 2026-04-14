from enum import Enum

class params:
    def __init__(self):
        self.globalParameters = {
            parameterType.AIRCRAFT_STATE : {
                "airspeed"          : ["sim/cockpit2/gauges/indicators/airspeed_kts_pilot",80, 0,0,0,0],
                "roll"              : ["sim/cockpit2/gauges/indicators/roll_AHARS_deg_pilot",20,0,0,0,0],
                "heading"           : ["sim/cockpit2/gauges/indicators/heading_AHARS_deg_mag_pilot",179,0,0,0,0], # Previous Heading
                "latitude"          : ["sim/flightmodel/position/latitude",39.875027,0,0,0,0],
                "longitude"         : ["sim/flightmodel/position/longitude",-104.696482,0,0,0,0],
                "altitude"          : ["sim/flightmodel/position/y_agl",0,0,0,0,0],
                "pitch"             : ["sim/flightmodel/position/true_theta",0,0,0,0,0],
                "brakes"            : ["sim/cockpit2/controls/parking_brake_ratio",0,0,0,0,0],
                "wheelSpeed"        : ["sim/flightmodel2/gear/tire_rotation_speed_rad_sec",0,0,0,0,0],
                "wheelWeight"       : ["sim/flightmodel/parts/tire_vrt_def_veh",0,0,0,0,0],
                "flaps"             : ["sim/flightmodel/controls/flaprqst",0,0,0,0,0],
                "slip_skid"         : ["sim/cockpit2/gauges/indicators/slip_deg",0,0,0,0,0],
                "vertical_speed"    : ["sim/cockpit2/gauges/indicators/vvi_fpm_pilot",-400,0,0,0,0]
            },
            parameterType.AIRCRAFT_CONTROLS: {
                aircraftControls.YOKE_PULL : [0],
                aircraftControls.YOKE_STEER : [0],
                aircraftControls.RUDDER : [0],
                aircraftControls.THROTTLE: [0]
            },
            parameterType.PHASE_FLAGS: {
                flightPhase.DESCENT.value         : [True],
                flightPhase.FLARE.value           : [False],
                flightPhase.ROLLOUT.value         : [False]
            },
            parameterType.INTEGRAL_VALUES : {
                integralValues.K : [integralValues.K.value], # Proportional gain
                integralValues.Ki : [integralValues.Ki.value]  # Integral gain  
            },
            parameterType.TIMING: {
                timeValues.DELTA_T: 0.15
            },
            parameterType.VISION_QUEUE: { 
                ## Basic Simulator of a scan order (FIFO) for vision module
                visionModule.QUEUE.value: [],
                visionModule.POINTER_1.value: [0]
            }
        }

    def dictionaryAccess(self,keys : list,accessItem,permissionFlag,inputValue=None):
        nestedDictionary = self.globalParameters
        for key in keys:
            result = nestedDictionary[key]
            nestedDictionary = result
        # vision = self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value][self.globalParameters[parameterType.VISION_QUEUE][visionModule.POINTER_1.value][0]:self.globalParameters[parameterType.VISION_QUEUE][visionModule.POINTER_1.value][0] + 8]
        if(permissionFlag == permissions.WRITE.value 
        #    and vision.__contains__(keys.pop())
           ):
            if isinstance(result, list):
                previous = result[accessItem]
                result[accessItem] = inputValue
                ## If updating a current valu in aircraft state, 
                # then update the previous now as well and recalculate the theta value and the delta from target
                if(accessItem == listAccess.CURRENT.value and keys[0] == parameterType.AIRCRAFT_STATE):
                    ## Setting Previous to Just Changed Value 
                    result[listAccess.PREVIOUS.value] = previous
                    ## Setting Delta Theta as change in degrees from previous to current
                    result[listAccess.DELTA_THETA.value] = inputValue - previous
                    # Setting Theta Value (Target - Current)
                    result[listAccess.THETA.value] = result[listAccess.TARGET.value] - inputValue
        else:
            if isinstance(result, list):
                return result[accessItem]
            else: 
                return result
    ## VISION 
    def populateVisionQueue(self):
        dictionary :dict = self.globalParameters.get(parameterType.AIRCRAFT_STATE)
        values = dictionary.keys()
        queue = []
        for item in values:
            queue.append(item)
        # print("Vision Queue Populated: " + str(queue))
        self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value] = queue
        # print("Vision Queue: " + str(self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value]))

    def visionCycle(self):
        if(self.globalParameters[parameterType.VISION_QUEUE][visionModule.POINTER_1.value][0] <= len(self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value]) - 0):
            self.globalParameters[parameterType.VISION_QUEUE][visionModule.POINTER_1.value][0] += 1
        else: 
            self.globalParameters[parameterType.VISION_QUEUE][visionModule.POINTER_1.value][0] = 0
        # queue :list = self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value]
        # firstItem = queue.pop(0)
        # queue.append(firstItem)
        # self.globalParameters[parameterType.VISION_QUEUE][visionModule.QUEUE.value] = queue
    
    def getModelDREFS(self):
        dictionary :dict = self.globalParameters.get(parameterType.AIRCRAFT_STATE)
        values = dictionary.values()
        drefList = []
        for item in values:
            drefList.append(item[listAccess.DREF.value])
        return drefList
    
    def getModelKeys(self):
        dictionary :dict = self.globalParameters.get(parameterType.AIRCRAFT_STATE)
        keys = dictionary.items()
        keyList = []
        for item in keys:
            keyList.append(item[0])
        return keyList
    
    def printParameter(self,allowPrinting):
        if(not allowPrinting):
            return
        dictionary :dict = self.globalParameters.get(parameterType.AIRCRAFT_STATE)
        keys = dictionary.items()
        itemList = []
        paramList = []
        targetList = []
        previousList = []
        deltaThetaList = []
        thetaList = []

        for item in keys:
            itemList.append(item[0])
            paramList.append(str(item[1][listAccess.CURRENT.value]))
            targetList.append(str(item[1][listAccess.TARGET.value]))
            previousList.append(str(item[1][listAccess.PREVIOUS.value]))
            deltaThetaList.append(str(item[1][listAccess.DELTA_THETA.value]))
            thetaList.append(str(item[1][listAccess.THETA.value]))

        dictionary2 :dict = self.globalParameters.get(parameterType.AIRCRAFT_CONTROLS)
        keys2 = dictionary2.items()
        for item in keys2:
            itemList.append(item[0].value)
            paramList.append(str(item[1]))
            targetList.append(0)
            previousList.append(0)
            deltaThetaList.append(0)
            thetaList.append(0)

        header_row = "{:<30} {:<30} {:<30} {:<30} {:<30} {:>20}"
        headers = "Parameter Current Target Previous Delta_Theta Theta".split()
        row = "{:<30} {:<30} {:<30} {:<30} {:<30} {:>20}"
        print("\n" + header_row.format(*headers))
        print("-" * 101)
        for parameter, current, target, previous,deltaTheta,theta in zip(itemList, paramList, targetList,previousList,deltaThetaList,thetaList):
            print(row.format(parameter,current, target, previous,deltaTheta,theta))
        # print(self.globalParameters[parameterType.AIRCRAFT_STATE]["airspeed"][listAccess.CURRENT])


    def initialize(self):
        self.populateVisionQueue()

class listAccess(Enum):
    DREF = 0
    TARGET = 1
    PREVIOUS = 2
    CURRENT = 3
    THETA = 4
    DELTA_THETA = 5
    PHASE_FLAG = 0
    INTEGRAL_VALUE = 0
    TIMING = 0
    ## Aircraft Controls
    CONTROL_VALUE = 0

class parameterType(Enum):
    AIRCRAFT_STATE = "aircraft_state"
    AIRCRAFT_CONTROLS = "aircraft_controls"
    PHASE_FLAGS = "phase_flags"
    INTEGRAL_VALUES = "integral_values"
    TIMING = "timing"
    VISION_QUEUE = "vision_queue"
class visionModule(Enum):
    QUEUE = "queue"
    POINTER_1 = "pointer_1"
    POINTER_2 = "pointer_2"
class aircraftControls(Enum):
    YOKE_PULL = "yoke_pull"
    YOKE_STEER = "yoke_steer"
    RUDDER = "rudder"
    THROTTLE = "vertical_speed"
class flightPhase(Enum):
    DESCENT =   "descent"
    FLARE   =   "flare"
    ROLLOUT =   "rollout"

class integralValues(Enum):
    K = 0.035
    Ki = 0.01

class timeValues(Enum):
    DELTA_T = "deltaT"

class permissions(Enum):
    READ = 0
    WRITE = 1