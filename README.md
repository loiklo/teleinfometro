# teleinfometro
French Enedis Teleinfo exporter

This code read the stream data from any electronic power meter from Enedis (even the old ones) and send the power meter to an Influxdb database in order to be graphed with Grafana.

To allow a fast deployment, this code doesn't use the InfluxDB client lib. It uses instead the REST interface.

The code should work with Windows since python-serial library works with Windows.

![teleinfometro.png](teleinfometro.png)

# Task List
- [x] Read stream from teleinfo serial port
- [x] Allow interval data aggregation to only send the average value to Influxdb
- [x] Send data to Influxdb
- [ ] Create routine/thread to send data at a user defined interval
- [ ] Create a linux systemd daemon
- [ ] Add the peak value with the average when pushing data to Influxdb
- [ ] Send the overall power consumption with a dedicated routine/thread
