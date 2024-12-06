import logging

from dataclasses import dataclass
from typing import Dict

from homeassistant.helpers.entity import EntityCategory

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .datatypes import ModbusMode, ModbusPollMode, ModbusDefaultGroups, ModbusGroup, ModbusDatapoint
from .datatypes import ModbusSelectData, ModbusNumberData

_LOGGER = logging.getLogger(__name__)

class ModbusDevice():
    def __init__(self, host:str, port:int, slave_id:int):
        self._client = ModbusTcpClient(host, port)
        self._slave_id = slave_id
        
        # Default properties
        self.manufacturer=None
        self.model=None
        self.sw_version=None

        # Initialize empty datapoints
        self.Datapoints: Dict[ModbusGroup, Dict[str, ModbusDatapoint]] = {}

        # Add default datapoints
        self.Datapoints[ModbusDefaultGroups.CONFIG] = { }
        self.Datapoints[ModbusDefaultGroups.UI] = {
            "Config Selection": ModbusDatapoint(Address=0, DataType=ModbusSelectData(category=EntityCategory.CONFIG)),
            "Config Value": ModbusDatapoint(Address=0, DataType=ModbusNumberData(category=EntityCategory.CONFIG, min_value=0, max_value=65535, step=1))
        }

    def twos_complement(self, number) -> int:
        if number >> 15:
            return -((number^0xFFFF) + 1)
        else:
            return number
    
    """ ******************************************************* """
    """ ************* FUNCTIONS CALLED ON EVENTS ************** """
    """ ******************************************************* """
    async def onBeforeRead(self):
        pass
    async def onAfterRead(self):
        pass

    """ ******************************************************* """
    """ *********** EXTERNAL CALL TO READ ALL DATA ************ """
    """ ******************************************************* """
    async def readData(self):
        await self.onBeforeRead()

        for group, datapoints in self.Datapoints.items():
            _LOGGER.debug("Checking group %s", group)
            if group.poll_mode == ModbusPollMode.POLL_ON:
                _LOGGER.debug("Reading group %s", group)
                await self.readGroup(group)
                _LOGGER.debug("Read group %s", group)
        
        await self.onAfterRead()

    """ ******************************************************* """
    """ ******************** READ GROUP *********************** """
    """ ******************************************************* """
    async def readGroup(self, group:ModbusGroup):
        # We read multiple registers in one message
        _LOGGER.debug("Reading group: %s", group)
        n_reg = len(self.Datapoints[group])
        first_key = next(iter(self.Datapoints[group]))
        first_address = self.Datapoints[group][first_key].Address
   
        if group.mode  == ModbusMode.INPUT:
            response = self._client.read_input_registers(first_address,n_reg,self._slave_id)
        elif group.mode  == ModbusMode.HOLDING:
            response = self._client.read_holding_registers(first_address,n_reg,self._slave_id)
            
        if response.isError():
            _LOGGER.debug("Error: %s", response)
            raise ModbusException('{}'.format(response))
        else:
            _LOGGER.debug("Read group success")
            for (dataPointName, data), newVal in zip(self.Datapoints[group].items(), response.registers):
                newVal_2 = self.twos_complement(newVal)
                
                if data.Scaling == 1.0:
                    data.Value = newVal_2
                else:
                    data.Value = newVal_2 * data.Scaling
                _LOGGER.debug("Key: %s Value: %s", dataPointName, data.Value)
                
    """ ******************************************************* """
    """ **************** READ SINGLE VALUE ******************** """
    """ ******************************************************* """
    async def readValue(self, group:ModbusGroup, key) -> float:
        # We read single register
        _LOGGER.debug("Reading value: %s - %s", group, key)

        if group.mode == ModbusMode.INPUT:
            response = self._client.read_input_registers(self.Datapoints[group][key].Address,1,self._slave_id)
        elif group.mode == ModbusMode.HOLDING:
            response = self._client.read_holding_registers(self.Datapoints[group][key].Address,1,self._slave_id)

        if response.isError():
            raise ModbusException('{}'.format(response))
        else:
            newVal_2 = self.twos_complement(response.registers[0])
            self.Datapoints[group][key].Value = newVal_2 * self.Datapoints[group][key].Scaling
        
        return self.Datapoints[group][key].Value

    """ ******************************************************* """
    """ **************** WRITE SINGLE VALUE ******************* """
    """ ******************************************************* """
    async def writeValue(self, group, key, value):
        # We write single holding register
        _LOGGER.debug("Writing value: %s - %s - %s", group, key, value)
        scaledVal = round(value/self.Datapoints[group][key].Scaling)
        scaledVal = self.twos_complement(scaledVal)
        response = self._client.write_register(self.Datapoints[group][key].Address, scaledVal, self._slave_id)
        if response.isError():
            raise ModbusException('{}'.format(response))
        else:
            self.Datapoints[group][key].Value = value
