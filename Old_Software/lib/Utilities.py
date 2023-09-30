from ulab import numpy as np

def moving_average(x, w):
        #Doesn't conserve size
        return np.convolve(x, np.ones(w)) / w

def weighted_moving_average(x,w):
    #w represents half the amount of points taken in consideration
    #Conserves size
    #Weights the points with 1/2^i where i is the distance to current point.
    n = x.size
    for i in range(n):
        rIndex = np.min((n,i+w))
        lIndex = np.max((0,i-w))
        newVal = 0
        dividor = 0
        for j in range(lIndex,rIndex):
            newVal = newVal + (x[j] / 2**(abs(i-j)))
            dividor = dividor + 1 / 2**(abs(i-j))
        if(dividor != 0):
            newVal = newVal / dividor        
        x[i] = newVal
    return x

def weighted_sum(x): #Method for the students to write??? Calculates the weighted mean of an array (weight = max( (1-(n-1-i)*0.01 ,0.2)) where n is the length of the array and i the index of the current element
    n = x.size()
    sum = 0
    weightsum = 0
    for i in range(n):
         weight = np.max((1-(n-1-i)*0.01,0.2))
         weightsum = weightsum + weight
         sum = sum + x[i]*weight
    return sum/weightsum

def remove_outlier(data,multiplier = 5,replace = True) : #Method for the students to write??? Removes outlier based on std and mean. All points outside of (+- Multiplier * std) of the mean are out
    mean = np.mean(data)
    std = np.std(data)
    maxdata = 0
    if(not replace):
        maxdata = np.max(data)       
    for i in range(data.size):
        if(abs(data[i] - mean) >= multiplier * std) :
            if(replace):
                data[i] = mean #replace all of the outliers with the mean if we should
            else:
                data[i] = maxdata+1
    if(not replace):
        data = data[data!= maxdata+1] #remove all of the outliers if we shouldn't replace them. Implementation could be better (Store Indices rather than change value?)
    return data
    
def find_peaks_np(array,window,compareNum):
    #Works only for 1-D arrays
    #Find peaks Method. Looks for Peaks in 2 * Window intervalls. Compares the peak with its compareNum Neighbors from either side 
    n = array.size
    indexes = np.zeros(n,dtype = np.uint16)
    maximums =np.zeros(n,dtype = np.float)
    nMax = 0
    i = window
    while (i < n - window):
        valid = True;
        localmax = np.argmax(array[i-window:i+window]) #Find the local maximum index in the intervall
        localmax = localmax + i - window #Calculate the absolute index out of the relative index
        if(nMax >= 1 and localmax == indexes[nMax-1]): #Skip if maximum has already been found
            i = i+window 
            continue
        rIndex = np.min((n-1,localmax + compareNum)) #Rightmost neighbor to compare with
        lIndex = np.max((0,localmax-compareNum)) # Leftmost neighbor to compare with
        for j in range(lIndex,localmax):
            if(array[j+1] - array[j] < 0): # If the Data isn't ascending from the leftmost neighbor until peak, it's invalid.
                valid = False
                break
        if(not valid) :
            i = i + window
            continue
        for j in range(localmax,rIndex):
            if(array[j+1]-array[j] > 0): # If the Data isn't descending from the peak until the rightmost neighbor, it's invalid.
                valid = False
                break
        if(not valid) :
            i = i + window #Skip if invalid
            continue          
        indexes[nMax] = localmax
        maximums[nMax] = array[localmax] #Add Values to array and increment nMax and i
        nMax = nMax + 1
        i = i + window
                
    return maximums[0:nMax],indexes[0:nMax]

def getDC(x,size):
    #Diese Methode Berechent DC-Antiel, basiert auf den Datenblatt, seite 31:https://pdfserv.maximintegrated.com/en/an/AN6409.pdf
    min,min_index= find_peaks_np(-x, window = 5,compareNum = 2) #replaced the getMIN method with my find peaks Method -Jad
    min = -min
    l=len(min)
    #aus dem Datenblatt (siehe link oben), ist DC anteil Minimale peak +/- ungefähr 20% der differenz zwischen ersten und letzten minimalen peak
    #DC anteil, orthogonal zu PEAK WERT
    #da roten signal stiegend/abfallend
    index0 = np.argmin(min)
    dc0 = min[index0]
    index1 = np.argmax(min)
    dc1 = min[index1]
    diff= dc1-dc0 
    if index0<index1:
        #größere maximum kommt zuerst-> abfallend
        dc=dc1 + diff*0.2  
    else:
        #Fur Roten signal:
        #da in diesen fall index der kleineren minimum zuerst kommt und AC anteil immer in die nähe der zweiten min
        dc=dc0-diff*0.2
        
    return dc,min_index

def getAC(x,size,peaks = None, peaksindex = None):
    #Die Funktion gibt zurück DC UND AC Antiel zurück, da die funktion schon getDC aufrufen muss, ist unnötig in hr_calc die Funktion 
    #getDC nochmal aufzurufen
    dc,min_index=getDC(x,size)
    if(peaks is None): #Added by Jad for efficiency. Peaks have already been found in the hr Method. Can't use it yet because Hr Data is moving averaged before finding peaks
        max,max_index= find_peaks_np(x, window = 5,compareNum = 2) #replaced the getMAX method with my find peaks Method -Jad
    else:
        max = peaks
        max_index = peaksindex
    l=len(max)
    ac_peak=np.max(max) 
    #AC Anteil ist differenz zwischen größten Peak und DC anteil    
    ac=ac_peak-dc
    return ac,dc 
