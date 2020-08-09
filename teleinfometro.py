#!/usr/bin/env python3

import serial
import requests
from datetime import datetime

################
### Settings
################
cfg_serial_port   = '/dev/ttyUSB0'
cfg_influxdb_host = 'http://influxdb.lan:8086/write?db=teleinfometro'
cfg_location      = 'myhouse'
cfg_debug         = False

################
### Initialize teleinfo serial port
################
serlink = serial.Serial()
serlink.port      = cfg_serial_port
serlink.baudrate  = 1200
serlink.bytesize  = serial.SEVENBITS
serlink.parity    = serial.PARITY_EVEN
serlink.stopbits  = serial.STOPBITS_ONE
serlink.exclusive = True
serlink.open()

################
### Debug printing
################
def print_debug(str):
  if cfg_debug == True:
    print('debug# ' + str)

################
### powerObj definition
################
class powerObj:
  """ An object that is modified between flush
  The objective is to:
  - feed this class with intermediate value
  - at defined interval: flush to an external time series database + reset
  """

  def __init__(self):
    self.power_avg  = 0 # Average power
    self.tick_ctr   = 0 # Number of value added
    self.power_peak = 0 # Top value recorded
    self.base       = 0 # Base (Total usage)

  def reset(self):
    """ Reset stats
    """
    self.power_avg  = 0
    self.tick_ctr   = 0
    self.power_peak = 0

  def debug_flush(self):
    """ Dump class variables
    """
    print_debug(
      'Average: ' + str(int(self.power_avg))
      + ' | Peak: ' + str(int(self.power_peak))
      + ' | Cpt: ' + str(self.tick_ctr)
    )

  def add_current_power(self, power_tick):
    """ Add a new power value to the class
    - Update the average value
    - Update the peak if needed
    """
    # Calculate the new running average
    self.power_avg = (self.power_avg * self.tick_ctr + power_tick) / (self.tick_ctr + 1)
    self.tick_ctr = self.tick_ctr + 1
    # Update the peak
    if power_tick > self.power_peak:
      self.power_peak = power_tick
    return True

  def update_base(self, current_base):
    """ Update base
    """
    self.base = current_base
    return True

  def influxdb_write(self):
    """ Send data into influxdb
    """
    # Time in nanoseconds for influxdb
    #current_time = int(datetime.utcnow().timestamp()*1000*1000*1000)
    current_time = int(datetime.now().timestamp()*1000*1000*1000)
    influxdb_host = cfg_influxdb_host
    influxdb_data = 'instant_power,location=' + cfg_location + ' value=' + str(int(self.power_avg)) + ' ' + str(current_time)
    influxdb_post = requests.post(
      url = influxdb_host,
      data = influxdb_data
    )
    print_debug('(instant_poser) Influxdb write return code: ' + str(influxdb_post.status_code))
    influxdb_data = 'base,location=' + cfg_location + ' value=' + str(int(self.base)) + ' ' + str(current_time)
    influxdb_post = requests.post(
      url = influxdb_host,
      data = influxdb_data
    )
    print_debug('(base) Influxdb write return code: ' + str(influxdb_post.status_code))
    return True

################
### Main
################
my_power = powerObj()

avg_bucket_cnt = 0

while True:
  # Read serial port for teleinfo data, line by line
  info_line = serlink.readline().decode()
  # Instant power consumption
  if info_line.startswith('PAPP'):
    current_power = int(info_line.split(" ")[1])
    print_debug('Conso: ' + str(current_power))
    my_power.add_current_power(current_power)
    my_power.debug_flush()

  if info_line.startswith('BASE'):
    current_base = int(info_line.split(" ")[1])
    print_debug('Base: ' + str(current_base))
    my_power.update_base(current_base)

  avg_bucket_cnt = avg_bucket_cnt + 1
  if avg_bucket_cnt == cfg_avg_bucket_size:
    my_power.influxdb_write()
    my_power.reset()
    avg_bucket_cnt = 0
