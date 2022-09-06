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
import numpy as np
from simple_pid import PID
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import fileout

kp, kd, ki = -7.0, -0.8, -0.6
min_pid, max_pid = -1.0, 1.0 #Volts
min_volt, max_volt = 50.0, 90.0 #Volts; max safe operating paremters [-1,]

#Setting the PID paremters.
pid = PID(kp, kd, ki)
pid.output_limits = (min_pid, max_pid)
pid.setpoint = 460.8623641 #nm



#voltage ramp for testing
def ramp(n, T, ymax, ymin):

    n_pulse = []

    def line( t, T, ymax, ymin):
        return (2*(ymax-ymin))/T * t + ymin

    def pulse_generator(T, ymax, ymin):
        n, N, pulse = 2, 1000, [] #number of point in the raising ramp
        time = np.linspace(0, T, N*n)
        for i in range(1, n+1):
            for t in time[(i-1)*N:i*N]:
                pulse.append( line( (-1)**(i+1)*(t - (i-1)*T) , T, ymax, ymin))
        return pulse

    for i in range(n):
        n_pulse += pulse_generator( T, ymax, ymin )

    return n_pulse

#########################################################
# laser locking test
#########################################################

date_time_stamp = datetime.now().strftime("%d-%m-%Y_%H%M")
filename = "Logdata_ramp"+f"_{date_time_stamp}"+".txt"
filename_meta = "Logmetedata_ramp"+f"_{date_time_stamp}"+".txt"
logfile = open(f"data/{filename}","a")
logfile_meta = open(f"data/{filename_meta}","a")

delay = 0.0001 #seconds
n = 1 #number of periods for the ramp

initial_voltage = 71.60
final_voltage   = 72.0

# Two kinds of ramps to use first is a triangle wave and the second is a linear ramp.
voltage_ramp = ramp(n, 1, final_voltage, initial_voltage) # triangle voltage_ramp
#voltage_ramp = np.linspace(initial_voltage, final_voltage, 1000)

wavelength_data, pc_measure, t = [], [], []
pid_voltege = []
pc_act = []

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

DLL_PATH = "wlmData.dll" #wavemeter path
try:
     wlmData.LoadDLL(DLL_PATH)
except:
     sys.exit("Error: Couldn't find DLL on path %s. Please check the DLL_PATH variable!" % DLL_PATH)

#adding meta data to the log file
logfile.write(f"=== Data ===\n")
logfile.write(f"Computer system time: {date_time_stamp}\n")
logfile.write("\ntime [s]\t mesure voltage [v]\t set voltage [v]\t wavelenth [nm]\n")

try:
    with DLCpro(SerialConnection('COM5')) as dlc:


        fileout.meta_data(pid, dlc)

        dlc.laser1.dl.pc.voltage_set.set(initial_voltage)# Settign the first voltage to the bottom of the ramp
        time.sleep(1) # Give time for the laser to settle. (idk how long this should be 1s is a guess)

        initial_time = time.time() # Time since the start of epoch in python; [seconds]

        for i in range( len(voltage_ramp) ):
            try:
                # Read Wavelength and check errors.
                Wavelength = wlmData.dll.GetWavelength(0.0)
                if Wavelength == wlmConst.ErrOutOfRange:
                    time.sleep(1)
                    Wavelength = wlmData.dll.GetWavelength(0.0)
                else:
                    wavelength_data.append(Wavelength)


                time.sleep(delay) # Ddjusting spaceing so that the data is taking at the aproprote time on ramp.

                # Testing with a linear ramp first
                pid_voltege.append( voltage_ramp[i] )

                # Checking that voltages are within a safe rage.
                if dlc.laser1.dl.pc.voltage_set.get() < initial_voltage-1 or dlc.laser1.dl.pc.voltage_set.get() > final_voltage+1 :
                    v_final = dlc.laser1.dl.pc.voltage_set.get() #getting final voltage
                    dlc.laser1.dl.pc.voltage_set.set(70) # set to a known sae votlage
                    raise Exception(f"Error: voltage out of set range. Final voltage was: {v_final}v")

                dlc.laser1.dl.pc.voltage_set.set(pid_voltege[-1])
                pc_measure.append(dlc.laser1.dl.pc.voltage_set.get())
                pc_act.append(dlc.laser1.dl.pc.voltage_act.get())
                t.append(time.time()-initial_time)
                time.sleep(delay) # Adding time delay to give to for the system to change?

                #Adding data to the log file
                logfile.write( f"{t[-1]}\t {pc_measure[-1]}\t {pc_act[-1]}\t {wavelength_data[-1]}\n")

                # Plotting data
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
except DeviceNotFoundError:
    print('Device not found')

logfile.close()
logfile_meta.close()
