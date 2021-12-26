# python-temperature-probe

This is a simple python3 script that uses the Adafruit SI7021 library to read temperature and relative humidity data
from an attached probe, and publish the data into a Google Cloud Pub/Sub topic for processing by other components.

## Setup

Before you can use this script, you need to have the necessary Python components installed. This assumes you already
have a working raspberry pi device with I2C enabled via `raspi-config`.

```
sudo apt-get install python3-pip
pip3 install RPI.GPIO
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-si7021
pip3 install paho-mqtt
pip3 install pyyaml
```

## Configuration

To install, clone the repo locally into `/home/pi/temp-probe-python`.

Create a GCP Service Account with permissions to publish to the desired topic. Export a key as `gcp_keys.json` and place
in the same folder.

Copy the `temp-probe.service` file into `/etc/systemd/system` adjusting the pathes as necessary.

Then, initalize the systemd components:

```
sudo systemctl daemon-reload
sudo systemctl enable temp-probe.service
sudo systemctl start temp-probe.service
```

You can check out the status of the service by running `systemctl status temp-probe.service`.

Logs for the app are written to `temp-probe.log` in the script's working directory.
