# This is an interface to arduino. It connects to it via the serial port, gathers data and 
# saves this data to a csv.
# It also manages the threshold and sends the corresponding on/off signal to arduino.
# It provides an interface via stdin to receive commands itself (coming from a node js server in this project)
import serial
import time
import sys
import threading
import io
import re
# flushing is necessary for communication via stdin/stdout
def printFlush(text):
    print(text)
    sys.stdout.flush()

printFlush('Ardoino Interface starting')
# connect to the right serial port (windows)
ser = serial.Serial('COM9', 9600, timeout=0)
# communication with node js is realised via stdin/stdout
_input = io.open(sys.stdin.fileno())
# wait for arduino to start 
time.sleep(2)
# get humidity and temperature from arduino and save to a csv together with the time
csvPath = 'C:/Users/Georg/Google Drive/Uni/Master/IS Engineering Course 3/sensordata.csv'
# current threshold is kept in a cfg file
cfgPath = 'C:/Users/Georg/Google Drive/Uni/Master/IS Engineering Course 3/threshold.cfg'
f = open(cfgPath, 'r')
threshold = float(f.read())
f.close()
# keep the current humidity available (start with fixed value, will be updated as soon as data is ready)
curHum = 40.0


def setThreshold(value):
    global threshold
    threshold = value
    f = open(cfgPath, 'w')
    f.write(str(value))
    f.close()

# a thread that waits for input from the node js server via the stdin
class waitForInput (threading.Thread):
    def __init__(self):
        super(waitForInput, self).__init__()
    
    def run(self):
        global ser
        global threshold
        global curHum
        global _input
        printFlush('waiting for command')
        while 1:
            cmd = _input.readline()
            printFlush('command received')
            if cmd == "on\n":
                printFlush('Turning on humidifier')
                ser.write(b'1')
                # turning on when the current humidity is under the current threshold
                # set the threshold to 100 so the humidifier stays on 
                if curHum > threshold:
                    print('Setting threshold to 100')
                    setThreshold(100)
            elif cmd == "off\n":
                printFlush('Turning off humidifier')
                ser.write(b'0')
                # turning off when the current humidity is over the current threshold
                # set the threshold to 0 so the humidifier stays off 
                if curHum < threshold:
                    print('Setting threshold to 0')
                    setThreshold(0)
            else:
                # set threshold (remove newline from end)
                setThreshold(float(cmd[:-1]))
                printFlush('Threshold updated to ' + cmd)

# a thread that reads data from arduino and saves it to the csv
# it also checks if the current humidity against the threshold and switches the humdifier on/off accordingly
class readData (threading.Thread):
    def __init__(self):
        super(readData, self).__init__()
        self.lastSignal = None

    def run(self):
        global ser
        global curHum
        printFlush('starting to read data')
        while 1:
            try:
                values = ser.readline().decode("utf-8")
                # every few seconds the values are received in the form:
                # 'humiditity-temperature' as floating point values

                # its possible to receive partial data at startup so make sure we receive a complete row
                pattern = re.compile("[0-9][0-9]\.[0-9][0-9]-[0-9]?[0-9]\.[0-9][0-9]")
                if pattern.match(values):
                    f = open(csvPath, 'a')
                    # the csv is in the form: date;humiditiy;temperature
                    newRow = '\n' + str(int(time.time()))
                    singleVals = values.split('-')
                    # add humidity and temperature to the row and save to csv
                    newRow += ";" + str(singleVals[0]) + ";" + str(singleVals[1])
                    f.write(newRow)
                    f.close()
                    printFlush(newRow + " added to csv")
                    # set current humidity and check if humidifier needs to be turned on/off
                    curHum = float(singleVals[0])
                    self.checkThreshold()
                time.sleep(1)
            except Exception as e:
                print(e)
                time.sleep(1)
        printFlush('done reading data')

    # checks whether humidifier needs to be turned on/off according to the threshold
    def checkThreshold(self):
        global curHum
        global ser
        global threshold
        if curHum < threshold:
            if self.lastSignal != 'on':
                ser.write(b'1')
                print('Humidifier turned on due to low humidity')
                self.lastSignal = 'on'
        if curHum > threshold:
            if self.lastSignal != 'off':
                ser.write(b'0')
                print('Desired humidity reached, turning off humidifier')
                self.lastSignal = 'off'


rd = readData()
wi = waitForInput()

wi.start()
rd.start()
# wait for threads to finish (they don't, currently both are in an infinity loop)
for t in [wi, rd]:
    t.join()
