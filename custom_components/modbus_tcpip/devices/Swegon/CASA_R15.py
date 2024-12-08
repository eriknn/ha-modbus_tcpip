from CASA_R4 import Device as BaseDevice

class Device(BaseDevice):
    def __init__(self, host:str, port:int, slave_id:int):
        super().__init__(host, port, slave_id)

        self.Datapoints[self.GROUP_SETPOINTS]["Temperature Setpoint"].Scaling = 1