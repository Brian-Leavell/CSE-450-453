# Need to have the network definition here to correctly load it in from the file

import torchaudio
import matplotlib.pyplot as plt#Need to download
import torch
import librosa
import torch.nn as nn
from scipy.signal import butter, sosfilt, firwin, lfilter

class DiagnosisNetwork(nn.Module):
  def __init__(self):
    super(DiagnosisNetwork, self).__init__()

    self.final_output_size = 3
    self.scalar_output_size = 64
    self.combined_input_size = 344
    
    self.convolution_pipeline_3d = nn.Sequential(
        nn.Conv2d(3, 24, kernel_size=(5, 5), stride=(4, 2), padding=0),
        nn.BatchNorm2d(24),
        nn.LeakyReLU(0.01),

        nn.Conv2d(24, 16, kernel_size=(5, 5), stride=(1, 1), padding=0),
        nn.BatchNorm2d(16),
        nn.LeakyReLU(0.01),

        nn.MaxPool2d(kernel_size=(4, 2), stride=(4, 2)),

        nn.Conv2d(16, 4, kernel_size=(3, 3), stride=(1, 1), padding=0),
        nn.BatchNorm2d(4),
        nn.LeakyReLU(0.01),
        nn.Flatten(),
    )
    

    self.scalar_pipeline = nn.Sequential(
        nn.Linear(1, 32),
        nn.LeakyReLU(0.01),
        nn.Linear(32, self.scalar_output_size),
        nn.LeakyReLU(0.01)
    )

    self.combined_pipeline = nn.Sequential(
        nn.Linear(self.combined_input_size, 1024),
        nn.BatchNorm1d(1024),
        nn.LeakyReLU(0.01),
        nn.Dropout(0.5),

        nn.Linear(1024, 512),
        nn.BatchNorm1d(512),
        nn.LeakyReLU(0.01),
        nn.Dropout(0.5),

        nn.Linear(512, 128),
        nn.BatchNorm1d(128),
        nn.LeakyReLU(0.01),
        nn.Dropout(0.5),

        nn.Linear(128, 64),
        nn.BatchNorm1d(64),
        nn.LeakyReLU(0.01),
        nn.Dropout(0.5),

        nn.Linear(64, self.final_output_size),
        nn.Softmax(dim=1)
    )


  def forward(self, input_2d_array, input_scalar):
    conv_flat = self.convolution_pipeline_3d(input_2d_array)
    scalar_output = self.scalar_pipeline(input_scalar)
    combined_output = torch.cat((conv_flat, scalar_output), dim=1)
    final_output = self.combined_pipeline(combined_output)
    return final_output


# For mode
# bell = 0, diaphragm = 1, extended = 2
def butter_bandpass_filter(data, lowcut, highcut, fs, order):
        sos = butter(N=order, Wn = [lowcut, highcut], btype = 'bandpass', output = 'sos', fs = fs)
        y = sosfilt(sos, data)
        return y

def fir_filter(data, cutoff, fs, num_taps):
    taps = firwin(num_taps, cutoff, fs=fs)
    y = lfilter(taps, 1.0, data)
    return y

def iir_filter(data, b, a):
    y = lfilter(b, a, data)
    return y


def prediction(filename, mode):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # do the preprocessing
    original_arr, sample_rate = torchaudio.load(filename)

    transform = torchaudio.transforms.Resample(sample_rate, 4000)
    resampled_arr = transform(original_arr)
    sample_rate = 4000
    """
    print(len(resampled_arr[0]))
    resampled_arr = resampled_arr[0][15000:25000]
    print(len(resampled_arr))
    """

    if mode == 0:
      lowcut = 20
      highcut = 200

    elif mode == 1:
      lowcut = 200
      highcut = 1999

    elif mode == 2:
      lowcut = 20
      highcut = 1999

    # Bandpass filter
    butter_filtered_audio = butter_bandpass_filter(resampled_arr, lowcut, highcut, sample_rate, 1)

    # FIR filter
    num_taps = 101
    filtered_audio_fir = fir_filter(butter_filtered_audio, [lowcut, highcut], fs=sample_rate, num_taps=num_taps)

    #filtered_audio_fir = filtered_audio_fir[0][15000:25000]

    # IIR filter
    b, a = [1.0], [1.0, -0.5]
    arr = torch.tensor(iir_filter(filtered_audio_fir, b, a))

    arr = arr.view(-1)

    # Generate MFCCs
    # Doing it this way makes the mfccs shape (20, 137)
    mfccs = librosa.feature.mfcc(y=arr.numpy(), sr=sample_rate)

    # Generate spectrogram image
    spectrogram = plt.specgram(arr, Fs=sample_rate)[0]
    plt.close()

    # Generate Chroma features
    chroma = librosa.feature.chroma_stft(y=arr.numpy(), sr=sample_rate)
    chroma_resized = torch.FloatTensor(chroma).unsqueeze(0).unsqueeze(0)
    chroma_resized = torch.nn.functional.interpolate(chroma_resized, size=(spectrogram.shape[0], spectrogram.shape[1]), mode='nearest')


    mfccs_resized = torch.FloatTensor(mfccs).unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions

    # Resize using interpolation to match the dimensions
    mfccs_resized = torch.nn.functional.interpolate(mfccs_resized, size=(spectrogram.shape[0], spectrogram.shape[1]), mode='nearest')

    # Convert spectrogram and mfccs to PyTorch tensors
    spectrogram_tensor = torch.FloatTensor(spectrogram).unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions

    # Concatenate along a new dimension to create a tensor with two channels
    combined_tensor = torch.cat((spectrogram_tensor,chroma_resized, mfccs_resized), dim=1).squeeze(0)

    combined_tensor = combined_tensor / 272.6519


    # Add x data row to x_data
    x_data = [combined_tensor, mode]

    # Load the network
    model = DiagnosisNetwork().to(device)
    model.load_state_dict(torch.load("skynet.pt", map_location=torch.device(device)))

    # Make the prediction
    with torch.no_grad():
        model.eval()

        input_2d_array, input_scalar = x_data
        # Reshape image and mode size for network

        # Format and add batch dimensions, the batch size will be 1 for both
        input_scalar = torch.tensor([input_scalar])
        input_scalar = input_scalar.unsqueeze(1)
        input_2d_array = input_2d_array.unsqueeze(0)

        # Correct types and send to device
        input_scalar = input_scalar.float()
        input_2d_array, input_scalar = input_2d_array.to(device), input_scalar.to(device)

        pred_probab = model(input_2d_array, input_scalar)
        yhat = int(pred_probab.argmax(1))

        # Convert network output to string output
        #final_conversion = ['asthma', 'copd', 'heart failure', 'lung fibrosis', 'murmur', 'n', 'plueral effusion', 'pneumonia']
        final_conversion =  ['asthma', 'heart failure', 'n']

        return final_conversion[yhat]

