import os
import time
from influxdb import InfluxDBClient
from datetime import datetime
from sense_hat import SenseHat

sense = SenseHat()
#defined wait time in milisec between measurements taken:
WAITTIME = 10000
LOCATION = 'Brew Sauna'

# get CPU temperature


def get_cpu_temp():
  res = os.popen("vcgencmd measure_temp").readline()
  t = float(res.replace("temp=", "").replace("'C\n", ""))
  return(t)

# use moving average to smooth readings


def get_smooth(x):
  if not hasattr(get_smooth, "t"):
    get_smooth.t = [x, x, x]
  get_smooth.t[2] = get_smooth.t[1]
  get_smooth.t[1] = get_smooth.t[0]
  get_smooth.t[0] = x
  xs = (get_smooth.t[0]+get_smooth.t[1]+get_smooth.t[2])/3
  return(xs)


def get_measurement():
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    t_cpu = get_cpu_temp()

    # calculates the real temperature compesating CPU heating
    t = (t1+t2)/2
    t_corr = t - ((t_cpu-t)/1.5)
    t_corr = get_smooth(t_corr)

    d = dict()
    d['temperature'] = t_corr
    d['humidity'] = sense.get_humidity()
    d['pressure'] = sense.get_pressure()
    return(d)


def write_measurement(m):
  if m['location']  is not None and m['timestamp'] is not None and m['humidity'] is not None and m['pressure'] is not None:
    json_body = [
      {
        "measurement": "brewpi",
        "tags": {
        "location": m['location']
      },
        "time": m['timestamp'],
        "fields": 
        {
          "temperature": m['temperature'],
          "humidity": m['humidity'],
          "pressure": m['pressure']
        }
      }
    ]

    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'brewpidb')
    return client.write_points(json_body)
  else:
    print("measurement not complete")
    return False

def main():
  while True:
    try:
      time_start = int(round(time.time() * 1000))

      #take measurement
      m = get_measurement()
      m['timestamp'] = time_start * 1000000 #influx nanosec precission
      m['location'] = LOCATION

      print(m)
      write_measurement(m)

      #take new time
      time_measurement = int(round(time.time() * 1000))

      # wait for: WAITTIME -(currentTime-new time)
      time_to_wait = float(WAITTIME - (time_measurement - time_start))

      print(time_to_wait/1000)

      time.sleep(time_to_wait/1000)
    
    except Exception as e:
      
      
      print(e)
      time.sleep(10)
      main()


main()
