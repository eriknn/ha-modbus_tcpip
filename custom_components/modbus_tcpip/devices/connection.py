class ConnectionParams:
    """Base class for connection parameters."""
    pass

class TCPConnectionParams(ConnectionParams):
    def __init__(self, ip: str, port: int, slave_id: int = 1):
        self.ip = ip
        self.port = port
        self.slave_id = slave_id

class RTUConnectionParams(ConnectionParams):
    def __init__(self, serial_port: str, baud_rate: int, slave_id: int = 1):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.slave_id = slave_id