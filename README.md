# Remote Stethoscope
### CSE 450/453 Hardware Software Integrated System Design
### University at Buffalo 2024
### Client: Dr. Robert Gatewood
### Professor: Dr. Kris Schindler
#### Tyler D'Angelo, Abiral Khadka, Brian Leavell, Rachel Li, Jacob Ryan, Bruno Sato, Arjun Suresh, Jacob Wen, Ian Witmer, Abidha Abedin, Alessandra Alessi

## Graphical User Interface
Uses Tkinter to create a GUI
- use buttons to select the filtering mode of the stethoscope between
  - Bell Mode (20 Hz to 200 Hz)
  - Diaphragm Mode (200 Hz to 2,000 Hz)
  - Wide Mode (20 Hz to 2,000 Hz)
- use a slider to adjust the volume of the filtered audio (slider does not yet change audio)
- use the text box to read any updates from the AI or doctor/patient application
- use a dropdown menu to select the audio input (not implemented)

## Audio Filtering
Uses PyAudio and SciPy
- pulls audio data from the computer's default audio input
- filtering the audio
  - filters audio with a slight delay 
  - filters at the same time as the rest of the application runs using threading
- sends filtered audio data to the computer's default audio output
- creating .wav files of audio to send to the AI

## Artificial Intelligence
Detects potential health problems, heart and lung

## Website
Uses React, JavaScript, CSS, PHP

## Encryption
Uses RSA encryption
- Encrypted data
  - information such as heart conditions are considered as Protected Health Information
  - sending PHI over unprotected connections is not HIPAA compliant
  - to send this information over unprotected connections, the data must be encrypted
  - the potential health problems detected by the AI model will be encrypted and sent from the patient to the doctor
- Encryption process
  - Doctor application creates a public-private key pair
  - Doctor application POSTs public key to the website
  - Patient application GETs public key from the website
  - Patient application encrypts data using the public key
  - Patient application POSTs encrypted data to the website
  - Doctor application GETs encrypted data from the website
  - Doctor application decrypts data using the private key

## Communication
Uses basic GET and POST requests
- the Doctor can control multiple aspects of the Remote Stethoscope application remotely
  - change the filtering mode by pushing the Bell, Diaphragm, and Wide buttons
  - change the volume of the filtered audio by using the Volume slider
- the Doctor can receive information from the Patient application remotely
  - AI potential health problems

## Executable File
Uses PyInstaller

### Version Information
- Python 3.11.8
- Tcl/Tk 8.6.12
- PyInstaller 6.5.0
