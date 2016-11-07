'''
Module to interface with a Zaber linear stage over a serial port.

Uses PySerial library for communication. Assumes Python 3.
'''

import serial
import atexit
import time

# use PySerial defaults for the other options
config = {'serial_port': 'COM1',
          'serial_baudrate': 9600,
          'serial_timeout': 0.5,
          'microsteps_per_micron': 6.4}

# Connection configuration
ser = serial.Serial()
ser.port = config['serial_port']
ser.baudrate = config['serial_baudrate']
ser.timeout = config['serial_timeout']

def open_connection():
    try:
        ser.open()
    except serial.SerialException:
        print('Serial connection could not be opened.')

def close_connection():
    _exit_cleanup()


def _exit_cleanup():
    ser.close()

atexit.register(_exit_cleanup)

def _read_and_get_pos():
    new_data = ser.read(6)
    data = new_data

    while new_data != b'':
        data = new_data
        new_data = ser.read(6)        
    
    # Device outputs 6 bytes.
    # Byte 1 is the device number, byte 2 is the instruction just completed.
    # Subsequent bytes are the data bytes.
    try:
        position_microsteps = int.from_bytes(data[2:], byteorder = 'little',
                                             signed = True)
        position_mm = position_microsteps / (config['microsteps_per_micron']
                                             * 1000.)
        print('Stage position (mm): ', position_mm)
    except IndexError:
        print('Data unsuccessfully read from device.')

        
def home():
    '''
    Home the stage.
    '''
    ser.write(bytearray([1, 1, 0, 0, 0, 0]))
    print('Moving stage to home position.')
    time.sleep(10)
    _read_and_get_pos()

    
def move(dist_mm):
    '''
    Move the stage relative to its current position. Positive values move
    forward, negative values move backward.

    dist_mm: distance to be traveled in mm. 
    '''
    dist_microns = dist_mm * 1000.
    dist_microsteps = dist_microns * config['microsteps_per_micron']
    # Need to round to nearest integer microstep
    rounded_dist_microsteps = int(round(dist_microsteps))

    # convert to bytes
    distance_bytes = rounded_dist_microsteps.to_bytes(4, byteorder = 'little',
                                                      signed = True)

    # First byte is device # (1), second is Zaber command number
    # Use command 21 (move relative)
    command = bytearray([1, 21]) + distance_bytes
    ser.write(command)
    time.sleep(0.5)
    _read_and_get_pos()


    ## TODO: we still have unexpected behavior where on a large move
    # initially the position of 0.0 is read. get_current_position()
    # run after the move is complete gets the correct position.

    
def get_current_position():
    command = bytearray([1, 60, 0, 0, 0, 0])
    ser.write(command)
    _read_and_get_pos()

    
