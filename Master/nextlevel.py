# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Remote Stethoscope                                      #
# CSE 450/453 Hardware/Software Integrated System Design  #
# University at Buffalo 2024                              #
# Client: Dr. Robert Gatewood                             #
# Professor: Dr. Kris Schindler                           #
# Computer Engineers:   Tyler D'Angelo                    #
#                       Abiral Khadka                     #
#                       Brian Leavell                     #
#                       Rachel Li                         #
#                       Jacob Ryan                        #
#                       Bruno Sato                        #
#                       Arjun Suresh                      #
#                       Jacob Wen                         #
#                       Ian Witmer                        #
# Mechanical Engineers: Abidha Abedin                     #
#                       Alessandra Alessi                 #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#####################
### I M P O R T S ###
#####################

# GUI Imports
import math
from tkinter import *
from tkinter import ttk

# PyAudio Imports
import wave
import sys
import os
import librosa
import soundfile as sf
import pyaudio
import threading
from scipy.signal import butter, sosfilt, sosfreqz
from scipy.io.wavfile import write
from scipy import signal
import numpy as np
import time

# AI Imports
import ai_production
from ai_production import DiagnosisNetwork


#######################################
### G L O B A L   V A R I A B L E S ###
#######################################

# GUI
# Window Size
window_width = 600
window_height = 525
# Grid Size
grid_width = 10
grid_height = 10
# Textbox location 
# used as a reference for other components
# can change these values to change the size of the textbox
tb_row_span = 3
tb_col_span = 5
# can change these valuse to change the position of the textbox
tb_row = 0
tb_col = 0

# Audio Filtering
CHUNK = 1050 #(originally 1024 but using this size for testing)
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

# Frequency Cutoffs
min_cutoff = 20
mid_cutoff = 200
max_cutoff = 2000
bell_low        = min_cutoff
bell_high       = mid_cutoff
diaphragm_low   = mid_cutoff
diaphragm_high  = max_cutoff
wide_low        = min_cutoff
wide_high       = max_cutoff
low_cutoff      = diaphragm_low
high_cutoff     = diaphragm_high

#Wave File Stuff
REC_SEC = 2.5
AI_start = False
arrayAudio = []
volume_scalar = 2
wavefilename = "test.wav"
ai_array = np.array([])
ai_array_size = 0 #fills at 7 with current timing
mode_code = 0 #0 is bell, 1 is diaphragm, 2 is wide


# Threading
# GUIActive is set to false when the GUI ends to break the thread running filtrationstation out
GUIActive = True
filtering = True
recording = False





#####################################
### A U D I O   F U N C T I O N S ###
#####################################

def butter_bandpass_filter(data, lowcut, highcut, fs, order):
        sos = butter(N=order, Wn = [lowcut, highcut], btype = 'bandpass', output = 'sos', fs = fs)
        y = sosfilt(sos, data)
        return y

def get_ai_output():
    global ai_array
    global wavefilename
    global mode_code
    global ai_array_size
    if (filtering):
        filteredfella = butter_bandpass_filter(ai_array, 20, 200, RATE, 5)
        filteredfella = filteredfella.astype(np.float32)
        sf.write(wavefilename, filteredfella, RATE)#generate the new file
        ai_output = ai_production.prediction(wavefilename, mode_code)#import from ai code, gives us a string to print
        insert_text(ai_output)#import this from the GUI code (thanks Tyler)
    ai_array = np.array([])#reset array
    ai_array_size = 0#allow array to start building again

    return

#Needs to be run on its own thread to filter audio in real-time. 
# Currently starts at the start of the program
def filtrationstation():
    global arrayAudio, recording, volume_scalar, volume, filtering, ai_array, ai_array_size
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output = True,
                        frames_per_buffer=15*CHUNK)
    
    while GUIActive:
        #Volume Slider Control
        final_volume_scalar = float(volume_scalar * volume.get() / 35)
        #Audio Stream
        data = stream.read(15*CHUNK)
        formatted = np.frombuffer(data, np.float32)
        convert16 = formatted.astype(np.float16)

        if (ai_array_size < 7):
            ai_array = np.append(ai_array,convert16)
            ai_array_size += 1
        else:
            get_ai_output()

        #Audio Stream Stuff
        filtered16 = convert16

        #Filters audio unless "No Filter" button is active
        if filtering:
            filtered16 = butter_bandpass_filter(convert16, low_cutoff, high_cutoff, RATE, 1)

        backto32 = (filtered16*final_volume_scalar).astype(np.float32)
        usable = backto32.tobytes()
        stream.write(usable)
    
    stream.stop_stream()
    stream.close()
    p.terminate()



#######################################
### B U T T O N   F U N C T I O N S ###
#######################################

# Button 1 Bell Mode
# Prints text to textbox when pressed
def but_bell():
    global low_cutoff, high_cutoff, filtering, mode_code, ai_array, ai_array_size
    low_cutoff = bell_low
    high_cutoff = bell_high
    filtering = True
    mode_code = 0
    ai_array = np.array([])#reset array
    ai_array_size = 0#allow array to start building again

    but_bell_mode["state"] = "disabled"
    but_diaphragm_mode["state"] = "normal"
    but_wide_mode["state"] = "normal"
    but_no_filter_mode["state"] = "normal"

    insert_text("Bell Mode")
    
# Button 2 Diaphragm Mode
# Prints text to textbox when pressed
def but_diaphragm():
    global low_cutoff, high_cutoff, filtering, mode_code, ai_array, ai_array_size
    low_cutoff = diaphragm_low
    high_cutoff = diaphragm_high
    filtering = True
    mode_code = 1
    ai_array = np.array([])#reset array
    ai_array_size = 0#allow array to start building again

    but_bell_mode["state"] = "normal"
    but_diaphragm_mode["state"] = "disabled"
    but_wide_mode["state"] = "normal"
    but_no_filter_mode["state"] = "normal"

    insert_text("Diaphragm Mode")
    
# Button 3 Wide Mode
# Prints text to textbox when pressed
def but_wide():
    global low_cutoff, high_cutoff, filtering, mode_code, ai_array, ai_array_size
    low_cutoff = wide_low
    high_cutoff = wide_high
    filtering = True
    mode_code = 2
    ai_array = np.array([])#reset array
    ai_array_size = 0#allow array to start building again

    but_bell_mode["state"] = "normal"
    but_diaphragm_mode["state"] = "normal"
    but_wide_mode["state"] = "disabled"
    but_no_filter_mode["state"] = "normal"
    
    insert_text("Wide Mode")
    
# Button 4 No Filtering Mode
# Prints text to textbox when pressed
def but_no_filter():
    global filtering
    filtering = False
    but_bell_mode["state"] = "normal"
    but_diaphragm_mode["state"] = "normal"
    but_wide_mode["state"] = "normal"
    but_no_filter_mode["state"] = "disabled"
    
    insert_text("No Filter")

# Insert Text
# Prints display_text text to textbox and adjusts scrollbar position to bottom 
def insert_text(display_text):
    text.insert(END, display_text + "\n") # inserts text at end of textbox
    text.yview_moveto(1.0) # sets scrollbar and textbox position to bottom
    #print(display_text) # prints to console
    


#######################################################
### G R A P H I C A L   U S E R   I N T E R F A C E ###
#######################################################

# Main Window
root = Tk()
root.geometry(str(window_width) + 'x' + str(window_height))
root.title("Remote Stethoscope")
root.resizable(False, False)
frm = ttk.Frame(root, padding=10)
frm.grid()

# Button Style
style_color = ttk.Style()
style_color.configure("color.TButton", background="white")
# Recording Button Style
style = ttk.Style()
style.configure("colorRed.TButton", background="red", foreground="Red")
style.map("colorRed.TButton", background=[('active', 'red')])


# Bell Mode Button
but_bell_mode = ttk.Button(frm, text="Bell", command=but_bell, style="color.TButton")
but_bell_mode.grid(column=0, row=tb_row_span, sticky="nesw")

# Diaphragm Mode Button
but_diaphragm_mode = ttk.Button(frm, text="Diaphragm", command=but_diaphragm)
but_diaphragm_mode.grid(column=1, row=tb_row_span, sticky="nesw")

# Wide Mode Button
but_wide_mode = ttk.Button(frm, text="Wide", command=but_wide)
but_wide_mode.grid(column=2, row=tb_row_span, sticky="nesw")

# No Filtering Mode Button
but_no_filter_mode = ttk.Button(frm, text="No Filter", command=but_no_filter)
but_no_filter_mode.grid(column=3, row=tb_row_span, sticky="nesw")

# Spacing Button, needed to fill in row with the images
but_spacing = ttk.Button(frm, text="", command=but_wide)
but_spacing.grid(column=0, row=tb_row_span+1, sticky="ns")
but_spacing["state"] = "disabled"

# Scrolling Text Box
scroll = ttk.Scrollbar(frm, orient='vertical')
scroll.grid(column=(tb_col+tb_col_span), row=tb_row, columnspan=1, rowspan=tb_row_span, sticky='ns')
text = Text(frm, font=("Georgia, 10"), yscrollcommand=scroll.set)
text.grid(column=tb_col, row=tb_row, columnspan=tb_col_span, rowspan=tb_row_span)
scroll.config(command=text.yview)

# Volume Slider
volume = DoubleVar()
# access volume with volume.get()
slider = Scale(frm, variable=volume, from_=1, to=100, orient=HORIZONTAL, label=" ")
slider.grid(column=tb_col, row=tb_row+tb_row_span+8, columnspan=tb_col_span//2, rowspan=1, sticky='we')
volume.set(35)



# Frequency Waves 
width_wave = 100
height_wave = 30
center_wave = height_wave // 2
x_increment = width_wave / 400
# width stretch
bell_factor = -0.02
diaphragm_factor = -0.08
wide_factor = -0.02
wide_increment = 1.00405
# height stretch
y_amplitude = 10
bellCanvas = Canvas(width=width_wave, height=height_wave, bg='white')
diaphragmCanvas = Canvas(width=width_wave, height=height_wave, bg='white')
wideCanvas = Canvas(width=width_wave, height=height_wave, bg='white')
# This positions the waves relative to the window 
# resizing the window has been disabled to keep them in one location
bellCanvas.place(relx=0.124, rely=0.837, anchor=CENTER)
diaphragmCanvas.place(relx=0.335, rely=0.837, anchor=CENTER)
wideCanvas.place(relx=0.55, rely=0.837, anchor=CENTER)
# create the coordinate list for the sin() curve, have to be integers
bellxy = []
diaphragmxy = []
widexy = []
for x in range(400):
    # x coordinates
    bellxy.append(x * x_increment)
    diaphragmxy.append(x * x_increment)
    widexy.append(x * x_increment)
    # y coordinates
    bellxy.append(int(math.sin(x * bell_factor) * y_amplitude) + center_wave)
    diaphragmxy.append(int(math.sin(x * diaphragm_factor) * y_amplitude) + center_wave)
    widexy.append(int(math.sin(x * wide_factor) * y_amplitude) + center_wave)
    wide_factor *= wide_increment
bellLine = bellCanvas.create_line(bellxy, fill='blue')
diaphragmLine = diaphragmCanvas.create_line(diaphragmxy, fill='green')
wideLine = wideCanvas.create_line(widexy, fill='red')



#################################
### P R O G R A M   S T A R T ###
#################################


threading.Thread(target=filtrationstation).start()
but_diaphragm_mode["state"] = "disabled"
root.mainloop()
GUIActive = False
recording = False
arrayAudio = []
