# Home assistant Custom component for Pax Calima

## Installation

Download using HACS or manually put it in the custom_components folder.

## Add device

The integration supports discovery of devices, so any fans should be automatically discovered.
If not you may try to add it manually through the integration configuration.

## Sensor data

The sensors for temp/humidity/light seem to be a bit inaccurate, or I'm not converting them correctly, so don't expect them to be as accurate as from other dedicated sensors.
The humidity sensor will show 0 when humidity is low!
Airflow is just a conversion of the fan speed based on a linear correlation between those two. This is a bit inaccurate at best, as the true flow will vary greatly depending on how your fan is mounted.


## Good to know

Speed and duration for boostmode are local variables in home assistant, and as such will not influence boostmode from the app. These variables will also be reset to default if you re-add a device.

Configuration parameters are read only on Home Assistant startup, and subsequently once every day, to get any changes made from elsewhere.

Fast scan interval refers to the interval after a write has been made. This allows for quick feedback when the fan is controlled and does not disconnect between reads. This fast interval will remain for 10 reads.

Setting speed to less than 800 RPM might stall the fan, depending on the specific application. I don't know if stalling like this could damage the fan/motor, so do this with care.

## Thanks

- [@PatrickE94](https://github.com/PatrickE94/pycalima) for the Calima driver
- [@MarkoMarjamaa](https://github.com/MarkoMarjamaa/homeassistant-paxcalima) for a good starting point for the HA-implementation
