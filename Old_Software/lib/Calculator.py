from ulab import numpy as np
from ulab import scipy as scipy
from Utilities import remove_outlier
from Utilities import find_peaks_np
from Utilities import weighted_moving_average
from Utilities import weighted_sum
from Utilities import getAC

#In Ulab .size and .shape are methods! --> .size() .shape()

class Calculator :

    def fr_calc(self,CircularBuffer):
        n = CircularBuffer.getNumel();
        Millis = CircularBuffer.getColumn(0)
        Red = CircularBuffer.getColumn(1)
        IR = CircularBuffer.getColumn(2)
        Red = remove_outlier(IR) #Filter outlier #TODO RED AND IR REVERSED
        IR = remove_outlier(Red)
        Red = Red - np.mean(Red) #Remove DC part
        IR = IR - np.mean(IR)
        Fs = n / ((Millis[n-1] - Millis[0])* 10**(-3))    # effective sampling rate in Hz.
        
        #Red FFT
        red_filtered = Red
        red_fft = scipy.signal.spectrogram(red_filtered) #In ulab red_filtered.size needs to be a power of 2
        fr = Fs/2 * np.linspace(0,1,int(n/2)) #Frequency axis is dependent on the Sampling frequency
        y_m = 2/n * abs(red_fft[0:fr.size()]) #Normalized and rectified spectrogram
        fr_1 = fr[fr>0.8]
        y_m_sub = y_m[fr>0.8] #Only frequencies over 0.8 Hz (48 bpm) are of interest
        y_m_sub = y_m_sub[fr_1 < 4] #Only frequencies over 0.8 Hz (48 bpm) and under 4 Hz (240bpm) are of interest
        fr_1 = fr_1[fr_1 < 4] #Adjust frequency axis accordingly
        max_freq_red = fr_1[np.argmax(y_m_sub)] #Search for the max frequency
        
        #IR FFT
        ir_filtered = IR
        ir_fft = scipy.signal.spectrogram(ir_filtered) #Everything is the same for IR
        y_m_1 = 2/n * abs(ir_fft[0:fr.size()])
        fr_1 = fr[fr>0.8]
        y_m_1_sub = y_m_1[fr>0.8]
        y_m_1_sub = y_m_1_sub[fr_1 < 4]
        fr_1 = fr_1[fr_1 < 4]
        max_freq_IR = fr_1[np.argmax(y_m_1_sub)]
        
        #6 Points Moving Average (3 from either side), smoothes out noise. Weights the points with 1/2^i where i is the distance to current point.
        Red = weighted_moving_average(Red,3)
        IR = weighted_moving_average(IR,3)

        #Find Peaks Red
        indRed= find_peaks_np(Red,window = 5,compareNum = 2)[1]; #Find peaks Method. Looks for Peaks in 2 * Window intervalls. Compares the peak with its compareNum Neighbors from either side 
        frequenzRed = np.zeros(indRed.size()-1)
        for i in range(1,indRed.size()) :
            #frequenzRed[i-1] = 10**(3) * 60 / (Millis[indRed[i]] - Millis[indRed[i-1]]) #frequenz in bpm
            frequenzRed[i-1] = Fs /(indRed[i] - indRed[i-1]) #Heart frequency is the Sampling frequency / the number of points between consecutive peaks
        
        frequenzRed = remove_outlier(frequenzRed,multiplier = 4,replace = False) # Also remove outliers in the frequency arrray
        #meanfreqRed = weighted_sum(frequenzRed)
        meanfreqRed = np.mean(frequenzRed) # End Frequency is the mean of all frequencies

        #Find Peaks IR
        indIR = find_peaks_np(IR,window = 5,compareNum = 2)[1]; # Same thing for IR
        
        frequenzIR = np.zeros(indIR.size()-1)
        for i in range(1,indIR.size()) :
            #frequenzIR[i-1]=10**(3) * 60 / (Millis[indIR[i]] - Millis[indIR[i-1]])
            frequenzIR[i-1] = Fs /(indIR[i] - indIR[i-1])
         
        frequenzIR = remove_outlier(frequenzIR,multiplier = 4,replace = False)
        #meanfreqIR = weighted_sum(frequenzIR)
        meanfreqIR = np.mean(frequenzIR)
        
        return np.array([max_freq_red*60,max_freq_IR*60,meanfreqRed*60,meanfreqIR*60]) #Return frequencies in bpm
    
    def spo2_calc(self,CircularBuffer):
        n = CircularBuffer.getNumel();
        Millis = CircularBuffer.getColumn(0)
        red_data = CircularBuffer.getColumn(1)
        ir_data = CircularBuffer.getColumn(2)
        x=remove_outlier(red_data) #Filtere Ausreißer raus.
        y=remove_outlier(ir_data)
        n_new = n
        redAC,redDC= getAC(x,n)  #DC anteil,Get AC Peak-to-Peak from RED signal ,berechnung DC antiel hier beschrieben:https://pdfserv.maximintegrated.com/en/an/AN6409.pdf
        irAC,irDC= getAC(y,n) #DC anteil,Get AC Peak-to-Peak from IR signal 
        nume=redAC/redDC #Ratio berechnung
        denom=irAC/irDC
        ratio_ave=denom/nume  #SIGNALEN VERTAUSCHT? 
        print("ratio average: ", ratio_ave,"Nume:",nume,"Denom:",denom)
        while((ratio_ave < 0 or ratio_ave > 5) and n_new >= 64) : #Von Jad. Versuche einen validen ratio_ave zu kriegen, indem die ältere Hälfte der Daten jedes mal ausgeschnitten wird, bis es min 32 Datenpunkte gibt
            x = x[int(n_new / 2) : n_new - 1]
            y = y[int(n_new / 2) : n_new - 1]
            n_new = int(n_new/2)
            redAC,redDC= getAC(x,len(x))
            irAC,irDC= getAC(y,len(y))
            nume=redAC/redDC
            denom=irAC/irDC
            ratio_ave=denom/nume
            print("ratio average: ", ratio_ave,"Nume:",nume,"Denom:",denom)        
        #https://pdfserv.maximintegrated.com/en/an/SpO2-Measurement-Maxim-MAX32664-Sensor-Hub.pdf
        #Ratio_Ave=[0.5,2] --->(link,seite11)       
        if ratio_ave > 0 and ratio_ave < 5:
            ##Formel von arduino forum
            # -45.060 * ratioAverage * ratioAverage / 10000 + 30.354 * ratioAverage / 100 + 94.845
            spo2 = -45.060 * (ratio_ave**2) + 30.054 * ratio_ave + 94.845
            spo2_valid = True
        else:
            spo2 = -999
            spo2_valid = False
            
        return spo2, spo2_valid
    
    def hr_spo2_calc(self,CircularBuffer):
        n = CircularBuffer.getNumel();
        Millis = CircularBuffer.getColumn(0)
        Red = CircularBuffer.getColumn(1)
        IR = CircularBuffer.getColumn(2)
        Red = remove_outlier(Red) #Filter outlier
        IR = remove_outlier(IR)
        Redhr = Red - np.mean(Red) #Remove DC part only for Heart Rate
        IRhr = IR - np.mean(IR)
        Fs = n / ((Millis[n-1] - Millis[0])* 10**(-3))    # effective sampling rate in Hz.
        
        #Red FFT
#         red_filtered = Redhr #Used to filter the data with a bandpass, don't anymore
#         red_fft = scipy.signal.spectrogram(red_filtered) #In ulab red_filtered.size needs to be a power of 2
#         fr = Fs/2 * np.linspace(0,1,int(n/2)) #Frequency axis is dependent on the Sampling frequency
#         y_m = 2/n * abs(red_fft[0:fr.size()]) #Normalized and rectified spectrogram
#         fr_1 = fr[fr>0.8]
#         y_m_sub = y_m[fr>0.8] #Only frequencies over 0.8 Hz (48 bpm) are of interest
#         y_m_sub = y_m_sub[fr_1 < 4] #Only frequencies over 0.8 Hz (48 bpm) and under 4 Hz (240bpm) are of interest
#         fr_1 = fr_1[fr_1 < 4] #Adjust frequency axis accordingly
#         max_freq_red = fr_1[np.argmax(y_m_sub)] #Search for the max frequency
#         
        #IR FFT
#         ir_filtered = IRhr
#         ir_fft = scipy.signal.spectrogram(ir_filtered) #Everything is the same for IR
#         y_m_1 = 2/n * abs(ir_fft[0:fr.size()])
#         fr_1 = fr[fr>0.8]
#         y_m_1_sub = y_m_1[fr>0.8]
#         y_m_1_sub = y_m_1_sub[fr_1 < 4]
#         fr_1 = fr_1[fr_1 < 4]
#         max_freq_IR = fr_1[np.argmax(y_m_1_sub)]
        
        #6 Points Moving Average (3 from either side), smoothes out noise. Weights the points with 1/2^i where i is the distance to current point. Only for Heart rate.
        Redhr = weighted_moving_average(Redhr,3)
        IRhr = weighted_moving_average(IRhr,3)

        #Find Peaks Red
        peaksRed,indRed= find_peaks_np(Redhr,window = 5,compareNum = 2); #Find peaks Method. Looks for Peaks in 2 * Window intervalls. Compares the peak with its compareNum Neighbors from either side 
        frequenzRed = np.zeros(indRed.size-1)
        for i in range(1,indRed.size) :
            #frequenzRed[i-1] = 10**(3) * 60 / (Millis[indRed[i]] - Millis[indRed[i-1]]) #frequenz in bpm
            frequenzRed[i-1] = Fs /(indRed[i] - indRed[i-1]) #Heart frequency is the Sampling frequency / the number of points between consecutive peaks
        
        frequenzRed = remove_outlier(frequenzRed,multiplier = 4,replace = False) # Also remove outliers in the frequency arrray
        #meanfreqRed = weighted_sum(frequenzRed)
        meanfreqRed = np.mean(frequenzRed) # End Frequency is the mean of all frequencies

        #Find Peaks IR
        peaksIR,indIR = find_peaks_np(IRhr,window = 5,compareNum = 2); # Same thing for IR
        
        frequenzIR = np.zeros(indIR.size-1)
        for i in range(1,indIR.size) :
            #frequenzIR[i-1]=10**(3) * 60 / (Millis[indIR[i]] - Millis[indIR[i-1]])
            frequenzIR[i-1] = Fs /(indIR[i] - indIR[i-1])
         
        frequenzIR = remove_outlier(frequenzIR,multiplier = 4,replace = False)
        #meanfreqIR = weighted_sum(frequenzIR)
        meanfreqIR = np.mean(frequenzIR)
        
        #SPO2
        
#         n_new = n
#         redAC,redDC= getAC(Red,n)  #DC anteil,Get AC Peak-to-Peak from RED signal ,berechnung DC antiel hier beschrieben:https://pdfserv.maximintegrated.com/en/an/AN6409.pdf
#         irAC,irDC= getAC(IR,n) #DC anteil,Get AC Peak-to-Peak from IR signal 
#         nume=redAC/redDC #Ratio berechnung
#         denom=irAC/irDC
#         ratio_ave=denom/nume  #SIGNALEN VERTAUSCHT? 
#         while((ratio_ave < 0.41 or ratio_ave > 0.79) and n_new >= 64) : #Von Jad. Versuche einen validen ratio_ave zu kriegen, indem die ältere Hälfte der Daten jedes mal ausgeschnitten wird, bis es min 32 Datenpunkte gibt
#             Red = Red[int(n_new / 2) : n_new - 1]
#             IR = IR[int(n_new / 2) : n_new - 1]
#             n_new = int(n_new/2)
#             redAC,redDC= getAC(Red,len(Red))
#             irAC,irDC= getAC(IR,len(IR))
#             nume=redAC/redDC
#             denom=irAC/irDC
#             ratio_ave=denom/nume
            
            
        #https://pdfserv.maximintegrated.com/en/an/SpO2-Measurement-Maxim-MAX32664-Sensor-Hub.pdf
        #Ratio_Ave=[0.5,2] --->(link,seite11)       
#         if ratio_ave > 0.41 and ratio_ave < 0.79:
#             ##Formel von arduino forum
#             # -45.060 * ratioAverage * ratioAverage / 10000 + 30.354 * ratioAverage / 100 + 94.845
#             spo2 = 3 * (ratio_ave**2) -29.659 * ratio_ave + 111.68
#             spo2_valid = True
#             print("Spo2 : " + str(spo2) + " Ratio_ave : " + str(ratio_ave))
#         else:
#             spo2 = -999
#             spo2_valid = False
                    
                    
        spo2 = 0
        spo2_valid = False
        #                max_freq_red, max_freq_IR
        return np.array([0*60,0*60,meanfreqRed*60,meanfreqIR*60, spo2, int(spo2_valid)],dtype = np.float) #Return frequencies in bpm (fftRed,fftIR,peaksRed,peaksIR) and spo2