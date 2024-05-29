# GUI imports
from tkinter import *
from tkinter import ttk
#///////////////////////////////////////////////////////////////
#PyAudio Imports
import wave
import sys
import pyaudio
import threading
import soundfile as sf
import librosa
#///////////////////////////////////////////////////////////////
# Custom Functions

from scipy.signal import butter, sosfilt, sosfreqz
from scipy.io.wavfile import write
from scipy import signal
import numpy as np

#def butter_bandpass(lowcut, highcut, fs, order=5):
#        nyq = 0.5 * fs
#        low = lowcut / nyq
#        high = highcut / nyq
#        sos = butter(order, [low, high], analog=False, btype='band', output='sos')
#        return sos

volume_scalar = 1
ai_array_size = 0 #fills at 7 with current timing
ai_array = np.array([])
mode_code = 0 #0 is bell, 1 is diaphragm, 2 is wide
has_recorded = 0
wavefilename = "test.wav"


def butter_bandpass_filter(data, lowcut, highcut, fs, order):
        sos = butter(N=order, Wn = [lowcut, highcut], btype = 'bandpass', output = 'sos', fs = fs)
        y = sosfilt(sos, data)
        return y



def get_ai_output():
    global ai_array
    global wavefilename
    global filtercode
    global ai_array_size
    filteredfella = butter_bandpass_filter(ai_array, 20, 200, RATE, 5)
    filteredfella = filteredfella.astype(np.float32)
    sf.write(wavefilename, filteredfella, RATE)#generate the new file
    ai_output = prediction(wavefilename, filtercode)#import from ai code, gives us a string to print
    insert_text(ai_output)#import this from the GUI code (thanks Tyler)
    ai_array = np.array([])#reset array
    ai_array_size = 0#allow array to start building again

    return



"""CHUNK = 1024
def myfunction(myfile):
    with wave.open(myfile, 'rb') as wf:
        # Instantiate PyAudio and initialize PortAudio system resources (1)
        p = pyaudio.PyAudio()

    # Open stream (2)
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

    # Play samples from the wave file (3)
        while len(data := wf.readframes(CHUNK)):  # Requires Python 3.8+ for :=
            stream.write(data)

    # Close stream (4)
        stream.close()

    # Release PortAudio system resources (5)
        p.terminate()

def streamfunction():
    p = pyaudio.PyAudio()

    buffer = []

    # Open stream (2)
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    sample_rate = 44100,
                    input = True,
                    frames_per_buffer = 1024)
    
    buffer = stream.read(1024)
    
    stream.close()

    # Release PortAudio system resources (5)
    p.terminate()

def playback_example():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "voice.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    myfunction(WAVE_OUTPUT_FILENAME)

def stream_example():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "voice.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output = True,
                        frames_per_buffer=CHUNK)

    while True:

    
        data = stream.read(CHUNK)
        stream.write(data)"""

CHUNK = 1050 #at rate of 44100, 105 chunks is exactly 2.5 seconds
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

#GUIActive is set to false when the GUI ends to break the thread running filtrationstation out
GUIActive = True

#Only one of the following three will be true at any time; by setting the corresponding mode to True and the rest to False
#(should be done on button press), we can switch while filter the audio is being passed through. Starts in Bell mode.
bell_mode = True
diaphragm_mode = False
wide_mode = False

#Needs to be run on its own thread to filter audio in real-time. Currently starts by pressing button "One A"
def filtrationstation():
    global ai_array
    global ai_array_size
    global has_recorded

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output = True,
                        frames_per_buffer=15*CHUNK)
    
    while GUIActive:

        while bell_mode:
            data = stream.read(15*CHUNK)
            print(data)
            formatted = np.frombuffer(data, np.float32)
            convert16 = formatted.astype(np.float16)

            if (ai_array_size < 7):
                #ai_array.append(convert16)
                ai_array = np.append(ai_array,convert16)
                ai_array_size += 1
            
            elif (has_recorded == 0):
                #threading.Thread(target=skynet).start()
                #write to wav file for testing
                filteredfella = butter_bandpass_filter(ai_array, 20, 200, RATE, 5)
                filteredfella = filteredfella.astype(np.float32)
                #filteredfella.export("test.wav", format = "wav")
                sf.write("test.wav", filteredfella, RATE)
                has_recorded = 1

            else:
                threading.Thread(target=get_ai_output).start()

            filtered16 = butter_bandpass_filter(convert16, 20, 200, RATE, 1)
            backto32 = (filtered16*volume_scalar).astype(np.float32)#use slider value instead of volume scalar
            usable = backto32.tobytes()
            stream.write(usable)

        while diaphragm_mode:
            data = stream.read(15*CHUNK)
            formatted = np.frombuffer(data, np.float32)
            convert16 = formatted.astype(np.float16)
            filtered16 = butter_bandpass_filter(convert16, 200, 2000, RATE, 1)
            backto32 = (filtered16*volume_scalar).astype(np.float32)
            usable = backto32.tobytes()
            stream.write(usable)

        while wide_mode:
            data = stream.read(15*CHUNK)
            formatted = np.frombuffer(data, np.float32)
            convert16 = formatted.astype(np.float16)
            filtered16 = butter_bandpass_filter(convert16, 20, 2000, RATE, 1)
            backto32 = (filtered16*volume_scalar).astype(np.float32)
            usable = backto32.tobytes()
            stream.write(usable)
    
    stream.stop_stream()
    stream.close()
    p.terminate()

def increase_volume():
    if (volume_scalar < 5):
        volume_scalar = volume_scalar + 1

def decrease_volume():
    if (volume_scalar > 1):
        volume_scalar = volume_scalar - 1


    

    


#mythread = Thread(target = myfunction)
#threading.Thread(target=stream_example).start()

#def runmythread():
#    mythread.start()
#b, a = butter_bandpass_filter(wave.open('taunt.wav','rb'), 10, 1000, 5000, order = 5)
#write('test.wav', 5000, filteredtaunt)
#filteredtaunt.export("test.wav", format = "wav")
#import librosa
#import soundfile as sf

#asarray, sr = librosa.load('taunt.wav')
#print(asarray)
#filteredfella = butter_bandpass_filter(asarray, 1000, 5000, sr, 5)
#filteredfella = butter_bandpass_filter(asarray, 5000, 10000, sr, 5)
#filteredfella = butter_bandpass_filter(asarray, 20, 1200, sr, 5)
#print(filteredfella)
#sf.write('test.wav', filteredfella, sr)
#sos = signal.butter(order = 5, [10,1000], btype = 'band', fs=1000, output='sos')
#filtered = signal.sosfilt(sos, wave.open('taunt.wav','rb'))

#For BELL mode use 20-200Hz, for Diaphragm use 200-2000Hz

#from pydub import AudioSegment

#tomod = AudioSegment.from_wav("taunt.wav")
#tomod = tomod + 9
#tomod.export("test.wav", format = "wav")

### I M P O R T S ###
#####################
from tkinter import  *
from tkinter import ttk


#######################################
### G L O B A L   V A R I A B L E S ###
#######################################

# Button 1 version
a = True

# Textbox and Scrollbar location
tbHeight = 5
tbWidth = 5
tbRow = 1
tbCol = 0

#######################################
### C U S T O M   F U N C T I O N S ###
#######################################

# Button 1 Version A
# Prints text to console and textbox when pressed
def but1A():
    print ("Button 1 A")
    text.insert(END, "Button 1 A pressed\n")  # inserts text at end of textbox
    text.yview_moveto(1.0)  # sets scrollbar and textbox position to bottom
    #myfunction('taunt.wav') # replace with bell mode audio
    #playback_example()
    threading.Thread(target=filtrationstation).start()
    bell_mode = True
    diaphragm_mode = False
    wide_mode = False

# Button 1 Version B
# Prints text to console and textbox when pressed
def but1B():
    print ("Button 1 B")
    text.insert(END, "Button 1 B pressed\n")  # inserts text at end of textbox
    text.yview_moveto(1.0)  # sets scrollbar and textbox position to bottom
    #myfunction('test.wav') # replace with diaphragm mode audio
    bell_mode = False
    diaphragm_mode = True
    wide_mode = False

# Button 2
# Prints text to console and textbox when pressed
# Switches Button 1 between Versions A and B
def but2A():
    print("Button 2 pressed")
    # switches button 1 to other version
    global a
    if a:
        but1.configure(text="One B", command=but1B)
    else:
        but1.configure(text="One A", command=but1A)
    a = not a
    text.insert(END, "Button 2 pressed\n")  # inserts text at end of textbox
    text.yview_moveto(1.0)  # sets scrollbar and textbox position to bottom

#######################################################
### G R A P H I C A L   U S E R   I N T E R F A C E ###
#######################################################

# Main Window
root = Tk()
root.geometry('800x600')
frm = ttk.Frame(root, padding=10)
frm.grid()

# Title Label
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)

# Button 1
but1 = ttk.Button(frm, text="One A", command=but1A)
but1.grid(column=1, row=0)

# Button 2
but2 = ttk.Button(frm, text="Two", command=but2A)
but2.grid(column=2, row=0)

# Scrolling Text Box
scroll = ttk.Scrollbar(frm, orient='vertical')
scroll.grid(column=(tbCol+tbWidth), row=tbRow, columnspan=1, rowspan=tbHeight)
scroll.grid(sticky='ns')
text = Text(frm, font=("Georgia, 10"), yscrollcommand=scroll.set, width=50, height=5)
text.grid(column=tbCol, row=tbRow, columnspan=tbWidth, rowspan=tbHeight)
scroll.config(command=text.yview)

root.mainloop()
GUIActive = False
bell_mode = False
diaphragm_mode = False
wide_mode = False

#threading.Thread(target=filtrationstation).start()


#///////////////////////////////////////////////////////////////
#TorchAudio Functions
