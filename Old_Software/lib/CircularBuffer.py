from ulab import numpy as np

class CircularBuffer :
    
    def __init__(self, shape, columnNames) :
        self.shape = shape
        self.buffer = np.zeros((shape[0],shape[1]),dtype = np.float)
        self.numel = np.zeros(shape[1],dtype=np.uint16)
        self.columnNames = columnNames;
        self.full = False;
        self.orderedbuffer = np.zeros((shape[0],shape[1]),dtype = np.float)
        self.ordered = True;
        
    def __str__(self):
        buf = self.getorderedbuffer(); 
        #buf = buf[0:self.getNumel(),:]
        return str(buf)
    
    def add(self,elements):
        self.ordered = False;
        s = elements.shape;        
        if(len(s) == 1):
            s = np.array([1,s[0]],dtype = np.uint16)
            elements = elements.reshape((1,s[1]))
            
        for i in range (s[1]):
            for j in range(s[0]):
                self.buffer[self.numel[i],i] = elements[j,i]
                self.numel[i] = self.numel[i] + 1
                if(self.numel[i] >= self.shape[0]):
                    self.full = True
                    self.numel[i] = self.numel[i] % self.shape[0]
    
    
    def getNumel(self) :
        if(self.full):
            return self.shape[0]
        else :
            return self.numel[0]
    
    def getorderedbuffer(self) :
        if(self.isEmpty()):
            return 0;
        if(self.ordered):
            return self.orderedbuffer
        buf = self.buffer[0:self.getNumel(),:]
        buf1 = buf[0:self.numel[0],:]
        buf2 = buf[self.numel[0]: ,:]
        self.orderedbuffer = np.concatenate((buf2,buf1))
        self.ordered = True;
        return self.orderedbuffer
        
    
    def getColumnNames(self, i = -1) :
        if(i <= -1):
            return self.columnNames
        elif (i < len(self.columnNames)):
            return self.columnNames[i]
        else :
            return -1
        
    def getElement(self,line,column):
        buf = self.getorderedbuffer();
        #buf = self.buffer[0:self.getNumel(),:]
        if(column >= 0 and column < self.shape[1]):
            if(line >= 0 and line < self.getNumel()):
                return buf[line,column]
        return -1
    
    def getColumn(self,column):
        buf = self.getorderedbuffer();
        #buf = self.buffer[0:self.getNumel(),:]
        if(column >= 0 and column < self.shape[1]):
            return buf[:,column]
        return -1
    
    def getLine(self,line):
        buf = self.getorderedbuffer();
        #buf = self.buffer[0:self.getNumel(),:]
        if(line >= 0 and line < self.getNumel()):
            return buf[line,:]
        return -1
    
    def isEmpty(self):
        return self.getNumel() == 0
    
    def clear(self):
        self.buffer = np.zeros((shape[0],shape[1]),dtype = np.float)
        self.orderedbuffer = np.zeros((shape[0],shape[1]),dtype = np.float)
        self.ordered = True;
        self.numel = np.zeros(shape[1],dtype=np.uint16)
        self.full = False;
        
#     def remove(self,indexArray):
#         self.buffer[indexArray[0],indexArray[1]] = 0
        
            
            
            
            
    