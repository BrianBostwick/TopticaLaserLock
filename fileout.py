# wlmData.dll related imports
import wlmData
import wlmConst

#toptica related imports
import matplotlib.pyplot as pyplot
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection, DeviceNotFoundError, DecopError, UserLevel
from toptica.lasersdk.utils.dlcpro import *

# others
import sys
import time
from datetime import datetime


class meta_data:

    def __init__(self, pid, dlc):

        date_time_stamp = datetime.now().strftime("%d-%m-%Y_%H%M")
        filename = "LogdataMeta"+f"_{date_time_stamp}"+".txt"
        self.file = open(f"data/{filename}","a")

        self.pid = pid
        self.dlc = dlc
        
        self.head()
        self.wlmData()
        self.topticaData()

        self.file.close()

    def head( self ):
        self.file.write("=== PID paremters ===\n")
        self.file.write(f"(kp, kd, ki) = {self.pid.tunings}\n")

    def wlmData( self ):
        # Meta data for wavemeter
        # Read temperaure
        self.file.write("=== Wavemeter summary ===\n")

        # Read Type, Version, Revision and Build number
        Version_type = wlmData.dll.GetWLMVersion(0)
        Version_ver = wlmData.dll.GetWLMVersion(1)
        Version_rev = wlmData.dll.GetWLMVersion(2)
        Version_build = wlmData.dll.GetWLMVersion(3)
        self.file.write("WLM Version: [%s.%s.%s.%s]\n" % (Version_type, Version_ver, Version_rev, Version_build))

        Temperature = wlmData.dll.GetTemperature(0.0)
        if Temperature <= wlmConst.ErrTemperature:
            self.file.write("Temperature: Not available\n")
        else:
            self.file.write("Temperature: %.1f °C\n" % Temperature)

        # Read Pressure
        Pressure = wlmData.dll.GetPressure(0.0)
        if Pressure <= wlmConst.ErrTemperature:
            self.file.write("Pressure: Not available\n")
        else:
            self.file.write("Pressure: %.1f mbar\n" % Pressure)

        # Read exposure of CCD arrays
        Exposure = wlmData.dll.GetExposure(0)
        if Exposure == wlmConst.ErrWlmMissing:
            self.file.write("Exposure: WLM not active\n")
        elif Exposure == wlmConst.ErrNotAvailable:
            self.file.write("Exposure: not available\n")
        else:
            self.file.write("Exposure: %d ms\n" % Exposure)

        # Read Ch1 Exposure mode
        ExpoMode = wlmData.dll.GetExposureMode(False)
        if ExpoMode == 1:
            self.file.write("Ch1 Exposure: Auto\n")

        # Read Pulse Mode settings
        PulseMode = wlmData.dll.GetPulseMode(0)
        if PulseMode == 0:
            PulseModeString = "Continuous Wave (cw) laser\n"
        elif PulseMode == 1:
            PulseModeString = "Standard / Single / internally triggered pulsed\n"
        elif PulseMode == 2:
            PulseModeString = "Double / Externally triggered pulsed\n"
        else:
            PulseModeString = "Othe\nr"
        self.file.write("Pulse mode: %s\n" %PulseModeString)

        # Read Precision (Wide/Fine)
        Precision = wlmData.dll.GetWideMode(0)
        if Precision == 0:
            PrecisionString = "Fine\n"
        elif Precision == 1:
            PrecisionString = "Wide\n"
        else:
            PrecisionString = "Function not available\n"
        self.file.write("Precision: %s\n" %PrecisionString)

    def topticaData(self ):
            self.file.write(f"{self.dlc.system_summary()}") # Laser data


# class data:
#
#     def __init__(self):
#
#         date_time_stamp = datetime.now().strftime("%d-%m-%Y_%H%M")
#         filename = "Logdata"+f"_{date_time_stamp}"+".txt"
#         self.logfile = open(f"data/{filename}","a")
#
#         self.wavelength_data = []
#         self.time = []
#         self.piazo_volt_measure = []
#         self.pid_volt_set = []
#
#     def time():
#
#
#     def write_data():
