import datetime
import glob
from math import cos, pi, sin, sqrt
import math
import os
import time
from time import sleep
import xpc
from cognitiveModel import AircraftLandingModel
import shutil
import csv
from enum import Enum
# from playsound import playsound
import threading as threading
from threading import Thread
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

class messageType(Enum):
    REGULAR = 1
    ERROR = 2

class conditionAccess(Enum):
    # Turbulence Experiments,Starting Altitude (AGL),Wind Layer Altitude,Wind Direction,Wind Speed,
    # Turbulence,Thermal Rate,Thermal Percent,Thermal Altitude,Cognitive Delay
    #NEW COLUMNS:
    # initial_GndSpd, starting_distance
    STARTING_ALT = 1
    WIND_LAYER_ALT = 2
    WIND_DIRECTION = 3
    WIND_SPEED = 4
    TURBULENCE = 5
    THERMAL_RATE = 6
    THERMAL_PERCENT = 7
    THERMAL_ALT= 8
    COGNITIVE_DELAY = 9
    INITIAL_GNDSPD=10
    STARTING_DIST=11

def eulerToQuat(psiInput,thetaInput,phiInput):
    psi = float(pi / 360 * psiInput)
    theta = float(pi / 360 * thetaInput)
    phi = float(pi / 360 * phiInput)
    q0 =  cos(psi) * cos(theta) * cos(phi) + sin(psi) * sin(theta) * sin(phi)
    q1 =  cos(psi) * cos(theta) * sin(phi) - sin(psi) * sin(theta) * cos(phi)
    q2 =  cos(psi) * sin(theta) * cos(phi) + sin(psi) * cos(theta) * sin(phi)
    q3 = -cos(psi) * sin(theta) * sin(phi) + sin(psi) * cos(theta) * cos(phi)
    e = sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)

    quat = [q0/e,q1/e,q2/e,q3/e]
    return quat

def loadFile(filename:str="/experiments/weather_files/weather.csv"):
    dir = Path(__file__).parent
    # print(f"Script Directory: {dir}")
    # filename = str(dir) + "/experiments/weather_files/weather.csv"
    # filename = str(dir) + "/experiments/weather_files/turbulence.csv"
    with open(str(dir) + filename,"r") as f:
        matrix = list(csv.reader(f,delimiter=','))
        # print(matrix)
        return matrix

def selectWeather(matrix,experimentNumber):
    return matrix[experimentNumber]


def startingLatLong(distance,direction,lat,long):
        print("Entered startingLatLong")
        """
        distance: meters
        direction: bearing in degrees (0 = North, 90 = East)
        lat, long: starting coordinates in degrees
        """
        R = 6371000  # Earth radius in meters

        # Convert to radians
        lat1 = math.radians(lat)
        lon1 = math.radians(long)
        bearing = math.radians(direction)
        print("Converted Radians BORF")
        # Compute new latitude
        value = (
            math.sin(lat1) * math.cos(distance / R) +
            math.cos(lat1) * math.sin(distance / R) * math.cos(bearing)
        )

        # Clamp to [-1, 1]
        value = max(-1, min(1, value))
        print("Value:{}".format(value))
        lat2 = math.asin(value)
        print("Computed New Latitude")
        # Compute new longitude
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(distance / R) * math.cos(lat1),
            math.cos(distance / R) - math.sin(lat1) * math.sin(lat2)
        )
        print("Computed New Longitude")

        # Convert back to degrees
        print("Finished startingLatLong")
        return math.degrees(lat2), math.degrees(lon2)

"""
Experiment setup function:
"""
def experimentSetUp(client:xpc,currentConditions,newExperiment,file):
    # input("Check The Loaded File Now")
    

    print("Entered: EXPERIMENTSETUP")
    if(newExperiment):
        #Location:
        groundLevel = 5434
        offset = float(currentConditions[conditionAccess.STARTING_ALT.value])
        altitudeFEET = groundLevel + offset
        altitudeMETERS = altitudeFEET/3.281
        altitude = altitudeMETERS
        print(str(altitude))
        # 39.96239,  -104.696032,
        endLat = 39.892760
        endLong = -104.696148
        lat, long = startingLatLong(float(currentConditions[conditionAccess.STARTING_DIST.value])*1852,359,endLat,endLong)

        location1 =  [20,   -998, lat, long, altitude, -998, -998, -998, -998]
        # testLocation = [20,   -998, 27.20579,  -80.08621, altitude, -998, -998, -998, -998] # 27.20579°N/80.08621°W
        data = [
            location1\
            ]
        client.sendDATA(data)

        print("Zero velocities")
        x = "sim/flightmodel/position/local_vx"
        y = "sim/flightmodel/position/local_vy"
        z = "sim/flightmodel/position/local_vz"
        client.sendDREF(x,0)
        client.sendDREF(y,0)
        client.sendDREF(z,0)

        print("Zero rotation")
        p = "sim/flightmodel/position/P"
        q = "sim/flightmodel/position/Q"
        r = "sim/flightmodel/position/R"
        client.sendDREF(p,0)
        client.sendDREF(q,0)
        client.sendDREF(r,0)

        print("set heading")
        orient = "sim/flightmodel/position/q"
        pitch = client.getDREF("sim/flightmodel/position/true_theta")
        roll = client.getDREF("sim/flightmodel/position/true_phi")
        
        orientCommand = eulerToQuat(179,0,0) # heading, pitch,Roll
        orientTest = [1.0,1.0,1.0,1.0] # heading, pitch,Roll

        print("ORIENT TO: " + str(orientCommand))
        client.sendDREF(orient,orientCommand)
        orientResult = client.getDREF(orient)
        print(str(orientResult))
        # client.pauseSim(False)

        #Weather:
        windLayer = "sim/weather/wind_altitude_msl_m[0]"
        windLayer2 = "sim/weather/wind_altitude_msl_m[1]"
        windLayer3 = "sim/weather/wind_altitude_msl_m[2]"
        windDirection = "sim/weather/wind_direction_degt[0]"
        windSpeed = "sim/weather/wind_speed_kt[0]"
            # windDirections = [50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0]
            # client.sendDREF(windDirection,windDirections)
            # winds = [50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0,50.0]
            # client.sendDREF(windSpeed,winds)
            # result = client.getDREF(windLayer)
            # print("Wind:" + str(result))

        print("Setting Wind Layers")
        client.sendDREF(windLayer,float(currentConditions[2]))
        # client.sendDREF(windLayer2,15000)
        # client.sendDREF(windLayer3,15000)
        print("Setting Wind Direction and Speed")
        client.sendDREF(windDirection,float(currentConditions[3]))
        print("Set 1")
        client.sendDREF(windSpeed,float(currentConditions[4]))
        print("Set 2")

        print("Setting Turbulence Level")
        turbulenceDREF = "sim/weather/turbulence[0]"
        client.sendDREF(turbulenceDREF,float(currentConditions[5]))

        print("Setting Thermals")
        thermalRateDREF = "sim/weather/thermal_rate_ms"
        thermalPercentDREF = "sim/weather/thermal_percent"
        thermalAltitudeDREF = "sim/weather/thermal_altitude_msl_m"
        client.sendDREF(thermalRateDREF,float(currentConditions[6]))
        client.sendDREF(thermalPercentDREF,float(currentConditions[7]))
        client.sendDREF(thermalAltitudeDREF,float(currentConditions[8]))

        client.pauseSim(True)
        client.pauseSim(False)
        print("Setting initial velocity")
        zInit = "sim/flightmodel/position/local_vz"
        client.sendDREF(zInit, float(currentConditions[conditionAccess.INITIAL_GNDSPD.value])/1.94384)

        print("Setting Fuel to Experiment Level")
        # fuel = "sim/aircraft/weight/acf_m_fuel_tot"
        fuel = "sim/flightmodel/weight/m_fuel"
        fuelLevels = [20,20]
        client.sendDREF(fuel, fuelLevels)
        print("setup complete")

        """
        Set orientation and Position
            1 - Time 
            3- Speeds: [3,   V-indicated, 3,   2, 2, -998, VindMPH, V trueMPHas, vtrue MPHgs],\
            16 - Angular Velocities
            17 - PitchRoll and Headings: [17,   Pitch, Roll,   Heading True, -998, -998, -998, -998, -998],\   
            18 - Angle of Attack
            20 - Latitude and Longitude
        """
        message = "Conditions are set as\n" \
        "Experiment #: {} \n"       \
        "Starting Altitude: {} \n"  \
        "Layer Altitude: {} \n"     \
        "Wind Direction: {} \n"     \
        "Wind Speed: {} \n"         \
        "Turbulence: {} \n"         \
        "Thermal Rate: {} \n"       \
        "Thermal Percent: {}\n"     \
        "Thermal Altitude: {}\n"    \
        "Cognitive Delay: {}\n".format(currentConditions[0],
                                       currentConditions[1],
                                       currentConditions[2],
                                       currentConditions[3],
                                       currentConditions[4],
                                        currentConditions[5],
                                        currentConditions[6],
                                        currentConditions[7],
                                        currentConditions[8],
                                        currentConditions[9])
        specialPrint(message,False,messageType.REGULAR)
    else:
        print("Experiment currently in progress, not resetting position and environmental conditions")
    currentDelay = float(currentConditions[9])
    return currentDelay

def printLoop(status,data):
    while(status):
        print(str(data))
    if(not status):
        print("Thread Should Finish Now")



    

def log(cogModel, file,timeElapsed,cycleLength): # Get and format data for logging in output file
    airspeedDREF = "sim/cockpit2/gauges/indicators/airspeed_kts_pilot"
    groundspeedDREF = "sim/flightmodel/position/groundspeed"
    rollDREF = "sim/cockpit2/gauges/indicators/roll_AHARS_deg_pilot"
    magneticHeadingDREF = "sim/cockpit2/gauges/indicators/heading_AHARS_deg_mag_pilot"
    latitudeDREF = "sim/flightmodel/position/latitude"  
    longitudeDREF = "sim/flightmodel/position/longitude" 
    verticalSpeedDREF = "sim/flightmodel/position/vh_ind_fpm"
    altitudeAGLDREF = "sim/flightmodel/position/y_agl"
    pitchDREF = "sim/flightmodel/position/true_theta"
    brakeDREF = "sim/cockpit2/controls/parking_brake_ratio"
    wheelSpeedDREF = "sim/flightmodel2/gear/tire_rotation_speed_rad_sec"
    wheelWeightDREF = "sim/flightmodel/parts/tire_vrt_def_veh"
    if(timeElapsed > cycleLength):
        sources = [latitudeDREF, longitudeDREF,altitudeAGLDREF, pitchDREF,rollDREF,groundspeedDREF]
        data = cogModel.client.getDREFs(sources)
        # data[5][0] = data[5][0] * 1.94384
        mainString = []
        # data = client.readDATA()
        precision = 6
        mainString.append(str(round(timeElapsed,precision)))
        mainString.append(",")
        for d in data:
            mainString.append(str(round(d[0],precision)))
            mainString.append(",")
        mainString[len(mainString)-1] = "\n"
        finalString = "".join(mainString)
        file.write(finalString)
        file.flush()
    # file.write(str(timeElapsed) + "," + str(data[0][0]) + "," + str(data[1][0]) + "," + str(data[2][0]) + "," + str(data[3][0]) +"\n")

def runExperiment(title,currentConditions,allowPrinting,isNewExperiment,experimentCount,file, stop_event: threading.Event):
    specialPrint("New Experiment\nSetting Up the Simulation",False,messageType.REGULAR)
    startTime = 0
    endTime = 0
    timeElapsed = endTime - startTime
    experimentInProgress = True
    timeoutLimit = 10
    newExperiment =  isNewExperiment
    while(timeElapsed <= timeoutLimit and experimentInProgress and (not stop_event.is_set())):
        try:
            with xpc.XPlaneConnect() as client:
                """
                Test Connection
                """
                client.getDREF("sim/test/test_float")

                """
                Setup Model
                """
                cogModel = AircraftLandingModel(client,allowPrinting)
                """
                Set Simulator Conditions
                """
                currentDelay = experimentSetUp(cogModel.client,currentConditions,newExperiment,file)
                
                """
                """
                cogModel.client.pauseSim(False)
                newExperiment = False
                """
                Single Experiment Loop
                """
                startTime = time.time()
                endTime =   time.time()
                elapsed =   endTime - startTime

                startTimeLogging = time.time()
                elapsedLogging = endTime - startTimeLogging
                loggingInterval = 1.0

                """Print Thread"""
                def printThreadFunction(parameters):
                    parameters.printParameter()

                while(experimentInProgress and (not stop_event.is_set())):
                    # print(stop_event.is_set())
                    elapsed = endTime - startTime
                    elapsedLogging = endTime - startTimeLogging
                    
                    if(elapsed > currentDelay):
                        cogModel.update_aircraft_state() 
                        cogModel.update_controls_simultaneously()
                        # client.pauseSim(False)          #Unpause Simulator
                        startTime = time.time()
                    # sleep(2)                     # Let Simulator Run 50 Milliseconds
                    if(elapsedLogging > loggingInterval):
                        log(cogModel,file,elapsedLogging,loggingInterval)
                        startTimeLogging = time.time()
                    experimentInProgress = cogModel.getSimulationStatus()
                    endTime = time.time()
        except:
            endTime = time.time()
            timeElapsed = endTime - startTime
            message = "Except detected\nStart Time: {a}\nEnd Time: {b}\n" \
            "Time Elapsed: -----> {c} ".format(a= startTime, b=endTime,c=timeElapsed)
            specialPrint(message,False,messageType.ERROR)
            continue

    """
    Parse End Condition outside of experiment loop: Succesful Run or Timeout-Induced End
    """
    if(timeElapsed >= timeoutLimit):
        print("Timeout[" + str(timeElapsed) +"]:"+"Error, please run test again")
    else: 
        print("Model has finished running")

    """
    Ask Experimenter if they would like to exit experiment battery early and not continue to the next experiment in the sequence 
    """
    exitExperimentLoop = False
    if(stop_event.is_set()):
        exitExperimentLoop = True
    else: 
        # exitDecision = input("Press 'y' or any key to continue, press 'n' to exit...")
        exitDecision = 'y'
        if(exitDecision == "n"):
            exitExperimentLoop = True
    
    # if(not stop_event.is_set()):
    #     exitDecision = input("Press 'y' or any key to continue, press 'n' to exit...")
    #     # exitDecision = "yes"
    
    # if(exitDecision == "n" or stop_event.is_set()):
    #     exitExperimentLoop = True
    # else:
    #     exitExperimentLoop = False

    return exitExperimentLoop

def setUp(xplaneFolderPath):
    file = open(xplaneFolderPath + "Data.txt", 'w')
    file.close()
    specialPrint("Data Collection File Ready",False,messageType.REGULAR)

def cleanUp(count,title,xplaneFolderPath):
    now = datetime.datetime
    dir = Path(__file__).parent.parent.parent.parent
    shutil.copy(str(xplaneFolderPath) + "Data.txt", str(dir) + "/Project_Data/Current Experiment/" + str(count)+ "_" + title + ".csv")
    specialPrint("Data File Ready",False,messageType.REGULAR)

    # shutil.copy("/Users/flyingtopher/X-Plane 11/Data.txt", "/Users/flyingtopher/Desktop/Test Destination/" + title + "_"+ count + "_" + str(now.now()) + "_" + ".txt")
    # dirname = os.path.dirname(__file__)
    # print("CLEAN UP: Data File Deleted and Reset")
    # specialPrint("Data File Ready",False,messageType.REGULAR)

def specialPrint(text, inputRequested,type):
    if(type == messageType.REGULAR):
        print("-" * 81)
        print('====> ', end='')
        print(text, end= " <====\n")
        print("-" * 81 + "\n")
        if(inputRequested):
            inputReceived = input()
            return inputReceived
    if(type == messageType.ERROR):
        print("*" * 81)
        print(text)
        print("*" * 81 + "\n")

# def countDown(seconds,startTime):
#     global remaining
#     while(remaining > 0):
#         remaining = seconds - (time.time() - startTime)
    

# def awaitInput(prompt):
#     userInput = input(prompt)


# def inputLoop(prompt,duration):
#     t1 = Thread(target=countDown(duration))
#     t2 = Thread(target=awaitInput(prompt))

#     t1.start()
#     t2.start()

#     t1.join()
#     t2

#     return userInput

def ex(stop_event: threading.Event, experiment_name : str,experiment_number : int,experiment_setup_file:str):
    """
    One Time experimental setup
    """
    if stop_event == None:
        stop_event = threading.Event()
        stop_event.clear()
    
    dir = Path(__file__).parent.parent.parent.parent
    prefix = ""
    if(experiment_name == "" or experiment_name == None):
        prefix = specialPrint("Please Enter Experiment Set Title, leave blank for trial runs", True, messageType.REGULAR) 
    else:
        prefix = experiment_name
    
    experimentConditionMatrix = loadFile(experiment_setup_file)
    startAt = 0
    if(experiment_number == "" or experiment_number == None):
        startAt = input("Start At Experiment #1 to " + str(len(experimentConditionMatrix)-1)) 
    else:
        startAt = experiment_number
    # startAt = input("Start At Experiment #1 to " + str(len(experimentConditionMatrix)-1))
    title = str(prefix + "--" + experimentConditionMatrix[0][0])
    specialPrint("Title is: " + title, False, messageType.REGULAR)
    allowPrinting = True
    isNewExperiment = True
    experimentCount = int(startAt)
    header = "Cycle Time,Latitude,Longitude,AltAGL, Pitch, Roll, GndSpd\n"

    # dir = Path(__file__).parent.parent.parent
    # dimkdir(exist_ok=True, parents=True)

    ## Current Experiment Folder Setup
    Path(str(dir) + "/Project_Data/Current Experiment").mkdir(exist_ok=True, parents=True)
    files = glob.glob(str(dir) + '/Project_Data/Current Experiment/*.csv')
    print("Here are the files\n")
    print(files)
    for f in files:
        os.remove(f)

    file2 = open(str(dir) + "/Project_Data/Current Experiment/CurrentExperimentList.txt", 'w')
    file2.close()
    file2 = open(str(dir) + "/Project_Data/Current Experiment/CurrentExperimentList.txt", 'a+')
    file2.write(str(title) + "\n")
    







    startTime = time.time()
    # xplaneFolderPath = filedialog.askdirectory(
    #     title="Select The X-Plane 11 Folder",
    #     initialdir="/",  # Optional: set initial directory
    #     # filetypes=(("Text files", "*.txt"), ("All files", "*.*")) # Optional: filter file types
    #     )
    xplaneFolderPath = "/Users/flyingtopher/Applications/X-Plane 11"

    """
    Experiment Loop
    """
    while(experimentCount<len(experimentConditionMatrix)):
        setUp(xplaneFolderPath)
        file = open(str(xplaneFolderPath) + "Data.txt", 'a')
        file.write(str(header)) #Write Header to File$
        currentConditions = experimentConditionMatrix[experimentCount]
        file2.write(str(experimentCount) +" // " + str(currentConditions))
        file2.flush()
        exitExperimentLoop = runExperiment(title,currentConditions,allowPrinting,isNewExperiment,experimentCount,file,stop_event)
        cleanUp(experimentCount,title,xplaneFolderPath)
        if(exitExperimentLoop or stop_event.is_set()):
            break
        experimentCount+=1
        endTime = time.time()
        elapsed = endTime-startTime
        file2.write(" " + str(elapsed) + "\n")
    """
    End of Experiments
    """
    now = datetime.datetime
    ##Adding something to copy all the battery files into a safe folder so they don't get overwritten
    shutil.copytree((str(dir) + "/Project_Data/Current Experiment"), (str(dir) + "/Project_Data/Data_Storage/" + title + " " + str(now.now())), dirs_exist_ok=True)
    specialPrint("Experiment Battery Complete", False,messageType.REGULAR)

if __name__ == "__main__":
    ex()


