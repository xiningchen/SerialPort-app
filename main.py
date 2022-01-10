# Serial port COM232 program for testing
# Xining Chen

import serial.tools.list_ports
import PySimpleGUI as sg
import serial
import threading
from time import sleep

FONT_SIZE = 12
NO_OPEN_PORT_MSG = "No ports opened..."
OPENED_PORT_MSG = "Port opened."
CLOSE_PORT_MSG = "Port closed."
PARITY_MAP = {'None': serial.PARITY_NONE,
              'Even': serial.PARITY_EVEN,
              'Odd': serial.PARITY_ODD,
              'Mark': serial.PARITY_MARK,
              'Space': serial.PARITY_SPACE}

openPortFlag = 0
serialData = []
serialDataLock = threading.Lock()
baudRate = 300
parity = serial.PARITY_NONE
byteSize = serial.EIGHTBITS
stopBits = serial.STOPBITS_ONE

config_column = [
    [
        sg.Text("Serial Port:", size=(8, 1), font=FONT_SIZE)
    ],
    [
        sg.Text("Baud Rate:  ", size=(8, 1), font=FONT_SIZE),
        sg.Combo([300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200], default_value=115200, font=FONT_SIZE, size=(15,1), key="-BAUD LIST-"),
    ],
    [
        sg.Text("Parity:  ", size=(8, 1), font=FONT_SIZE),
        sg.Combo(['None', 'Even', 'Odd', 'Mark', 'Space'], default_value='None', font=FONT_SIZE, size=(15,1), key="-PARITY LIST-"),
    ],
    [
        sg.Text("Byte Size:  ", size=(8, 1), font=FONT_SIZE),
        sg.Combo([5, 6, 7, 8], default_value=8, font=FONT_SIZE, size=(15,1), key="-BYTE LIST-"),
    ],
    [
        sg.Text("Stop Bits:  ", size=(8, 1), font=FONT_SIZE),
        sg.Combo([1, 1.5, 2], default_value=1, font=FONT_SIZE, size=(15,1), key="-STOP LIST-"),
    ],
    [sg.Button("Open Port", font=FONT_SIZE), sg.Button("Close Port", font=FONT_SIZE)],
    [sg.Text(NO_OPEN_PORT_MSG, font=FONT_SIZE, size=(22,12), key="-MSG-")],
    [sg.Button("Quit", font=FONT_SIZE)]
]
rw_column = [
    [
        sg.Text("Send data: ", font=FONT_SIZE),
        sg.Button("Send", font=FONT_SIZE)
    ],
    [
        sg.Multiline(size=(60, 15), key='-USER INPUT TEXTBOX-')
    ],
    [
        sg.Text("Received data: ", font=FONT_SIZE),
        sg.Button("Clear", font=FONT_SIZE)
    ],
    [
        sg.Multiline(size=(60, 15), key='-READ ONLY TEXTBOX-')
    ]
]

# Listener thread
class listenerThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        while openPortFlag == 1:
            if self.port.in_waiting != 0:
                res = serialDataLock.acquire(blocking=True, timeout=-1)
                if res:
                    readInput = self.port.read(self.port.in_waiting)
                    serialData.append(readInput.decode())
                    serialDataLock.release()
            else:
                sleep(0.25)
        exit()

# Get available ports
def getCOM232Ports(portType="com232"):
    comPorts = {}
    portList = []
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if portType in desc.lower():
            devName = port.split(".")[1]
            # hwidSplit = hwid.split()
            # loc = ""
            # for e in hwidSplit:
            #     if "location" in e.lower():
            #         loc = e.split("=")[1]
            portList.append(devName)
            comPorts[devName] = port
            # if not (loc in comPorts):
            #     comPorts[loc] = [(port, devName, desc, hwid)]
            # else:
            #     comPorts[loc].append((port, devName, desc, hwid))
            # comPorts.append([devName, loc])
    return portList, comPorts

# Main
if __name__ == '__main__':
    portList, comPorts = getCOM232Ports()
    selectedPort = None
    openedPort = None
    portReaderThread = None
    if len(portList) > 0:
        selectedPort = portList[0]
    config_column[0].append(sg.Combo(portList, default_value=selectedPort, font=FONT_SIZE, size=(15,1), key="-PORT LIST-"))
    layout = [
        [
            sg.Column(config_column),
            sg.VSeperator(),
            sg.Column(rw_column),
        ]
    ]
    gui = sg.Window("Com232 Testing GUI", layout)
    while 1:
        event, values = gui.read(timeout=250)
        if len(serialData) > 0:
            displayData = ''
            if serialDataLock.acquire(blocking=True, timeout=-1):
                for s in serialData:
                    displayData += s + '\n'
                serialData.clear()
                serialDataLock.release()
            if displayData != '':
                gui['-READ ONLY TEXTBOX-'].update(displayData)

        if event == 'Send' and openPortFlag == 1:
            openedPort.write(str.encode(values['-USER INPUT TEXTBOX-']))
            openedPort.flush()
        if event == 'Open Port' and openPortFlag == 0:
            openPortFlag = 1
            selectedPort = comPorts[values['-PORT LIST-']]
            baudRate = values['-BAUD LIST-']
            parity = PARITY_MAP[values['-PARITY LIST-']]
            byteSize = values['-BYTE LIST-']
            stopBits = values['-STOP LIST-']
            openedPort = serial.Serial(selectedPort, baudrate=baudRate, bytesize=byteSize, parity=parity,
                                        stopbits=stopBits, timeout=1)
            portReaderThread = listenerThread(openedPort)
            portReaderThread.start()
            gui['-MSG-'].update(OPENED_PORT_MSG)
        if event == 'Close Port' and openPortFlag == 1:
            openPortFlag = 0
            openedPort.close()
            portReaderThread.join()
            portReaderThread = None
            gui['-MSG-'].update(CLOSE_PORT_MSG)
        if event == 'Clear':
            gui['-READ ONLY TEXTBOX-'].update('')
        if event == 'Quit' or event == sg.WIN_CLOSED:
            openPortFlag = 0
            if portReaderThread is not None:
                portReaderThread.join()
            if openedPort is not None:
                openedPort.close()
            gui.close()
            break