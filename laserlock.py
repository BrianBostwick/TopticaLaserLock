# wlmData.dll related imports
import wlmData
import wlmConst
import fileout

#toptica related imports
import matplotlib.pyplot as pyplot
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection, DeviceNotFoundError, DecopError, UserLevel
from toptica.lasersdk.utils.dlcpro import *

# others
import sys
import time
from datetime import datetime
import numpy as np
from simple_pid import PID
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import ctypes

delay = 0.05  #Seconds
run_time = 60 #Seconds

kp, kd, ki = -1.2, -0.6, -0.4
min_pid, max_pid = -1.0, 1.0 #Volts
min_volt, max_volt = 50.0, 95.0 #Volts; max safe operating paremters [-1,]

#Setting the PID paremters.
pid = PID(kp, kd, ki)
pid.output_limits = (min_pid, max_pid)
pid.setpoint = 460.9928 #nm
#pid.setpoint = 460.8623641 #nm
wavelength_data,  t = [], []
pc_measure, pc_act, pid_voltege = [], [], []

plt.ion() #starting interactive mode in plt
fig = plt.figure(figsize=(7, 7))

ax1 = fig.add_subplot(211)  #plot for the wavelength
ax1.ticklabel_format(useOffset=False)
ax1.set_ylabel("wavelength [nm]")
ax1.yaxis.set_major_formatter(FormatStrFormatter('%.9f'))
line1, = ax1.plot(t, wavelength_data, '-')

ax2 = fig.add_subplot(212) #plot for the voltage on the piezo
ax2.ticklabel_format(useOffset=False)
ax2.set_ylabel("voltage [v]")
ax2.set_xlabel("time [s]")
ax2.yaxis.set_major_formatter(FormatStrFormatter('%.9f'))
line2, = ax2.plot(t, pc_measure, '-')


# Testing wavemeter connection
DLL_PATH = "wlmData.dll" # Wavemeter path
try:
     wlmData.LoadDLL(DLL_PATH)
except:
     sys.exit("Error: Couldn't find DLL on path %s. Please check the DLL_PATH variable!" % DLL_PATH)

date_time_stamp = datetime.now().strftime("%d-%m-%Y_%H%M")
filename = "Logdata"+f"_{date_time_stamp}"+".txt"
logfile = open(f"data/{filename}","a")

#adding meta data to the log file
logfile.write(f"=== Data ===\n")
logfile.write(f"Computer system time: {date_time_stamp}\n")
logfile.write("\ntime [s]\t measure voltage [v]\t act voltage [v]\t wavelenth [nm]\n")

#PID
try:
    with DLCpro(SerialConnection('COM5')) as dlc:

        #Creating meta data file
        fileout.meta_data(pid, dlc)

        #Checks the number of WLM server instance(s)
        if wlmData.dll.GetWLMCount(0) == 0:
            raise Exception("There is no running wlmServer instance(s).")

        initial_time = time.time() #Time since the start of epoch in seconds
        pid_voltege.append(dlc.laser1.dl.pc.voltage_set.get()) #Getting a startign point for the PID controler

        while( True ):
            try:
                #Read Wavelength and check errors. Loop will end if exception is rasied
                Wavelength = wlmData.dll.GetWavelength(0.0)
                if Wavelength == wlmConst.ErrOutOfRange:
                    time.sleep(1)
                    Wavelength = wlmData.dll.GetWavelength(0.0)
                    #raise Exception("Ch1 Error: Out of Range")
                elif Wavelength <= 0:
                    raise Exception("Ch1 Error code: %d" % Wavelength)
                else:
                    wavelength_data.append(Wavelength)

                #Getting the next voltage output from the PID conrtole
                pid_voltege.append( pid(wavelength_data[-1]) + pid_voltege[-1] )

                #Checking that voltages are within a safe rage.
                if dlc.laser1.dl.pc.voltage_set.get() < min_volt or dlc.laser1.dl.pc.voltage_set.get() > max_volt or pid_voltege[-1] < min_volt or pid_voltege[-1] > max_volt:
                    v = dlc.laser1.dl.pc.voltage_set.get() #Getting final voltage
                    raise Exception(f"Error: voltage out of set range. Final voltage was: {v}v.")

                #Updating the piezo voltage
                dlc.laser1.dl.pc.voltage_set.set(pid_voltege[-1])
                pc_measure.append(dlc.laser1.dl.pc.voltage_set.get())
                pc_act.append(dlc.laser1.dl.pc.voltage_act.get())
                t.append(time.time()-initial_time)
                time.sleep(delay) #Adding time delay to give to for the system to change?

                #Adding data to the log file
                logfile.write( f"{t[-1]}\t {pc_measure[-1]}\t {pc_act[-1]}\t {wavelength_data[-1]}\n")

                #Plotting data
                line1.set_ydata(wavelength_data)
                line1.set_xdata(t)
                ax1.set_ylim([min(wavelength_data),max(wavelength_data)])
                ax1.set_xlim([min(t),max(t)])
                line2.set_ydata(pc_measure)
                line2.set_xdata(t)
                ax2.set_ylim([min(pc_measure),max(pc_measure)])
                ax2.set_xlim([min(t),max(t)])
                fig.canvas.draw()
                fig.canvas.flush_events()

            except DecopError as error:
                print(error)

    logfile.close()
except DeviceNotFoundError:
    print('Device not found')
