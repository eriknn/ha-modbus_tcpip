# Home assistant Custom component for Modbus TCP/IP

## Installation

Download using HACS (add repository manually) or manually download and put it in the custom_components folder.

## Purpose of integration

This integration supports dynamically loading device drivers, meaning that you just need to add one file to support a new modbus device.
This file will contain everything modbus related (addresses, scaling etc), and also information related to Home Assistant entities - that is, 
what type of entity it is, units etc.

## Usage

Create a new device file (devices/manufacturer/devicemodel.py). This file needs to define the following:
* A "Device" class subclassing ModbusDevice:
* Group enums
* Datapoints for each of the previously defined groups

The class will have access to the callbacks:
* onBeforeRead - Called before the groups are polled
* onAfterRead - Called after the groups are polled. Use this if you need to do some calculations / special conversion etc.

Take a look at an existing device file as an example

## Supported Home Assistant entities

* Sensor
* Switch
* Number
* BinarySensor
* Select

It's easy too add support for more, so let me know if anything's needed.
