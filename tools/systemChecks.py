import psutil
import json
import socket
import platform
import bleak
import asyncio

class SystemHealthCheck:
    def __init__(self):
        self.cpuUsage = psutil.cpu_percent(interval=0.1)
        self.memUsage = psutil.virtual_memory()
        self.diskUsage = psutil.disk_usage("/")
        self.swapUsage = psutil.swap_memory()
        self.batteryHealth = psutil.sensors_battery()

        self.cpuCount = psutil.cpu_count()
        self.cpuFreq = psutil.cpu_freq()

        self.cpuModel = platform.processor()
        self.system = platform.system()

        self.dns = "8.8.8.8"
        self.port = 53
        self.connectivity = self.checkConnectivity()
        self.btConnection = self.checkBT()

    def checkConnectivity(self):
        try:
            socket.setdefaulttimeout(3)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("8.8.8.8", 53))
            return True
        except (socket.timeout, OSError):
            return False

    def checkBT(self):
        try:
            asyncio.run(bleak.BleakScanner.discover(timeout=1.0))
            return True
        except Exception:
            return False

    def checkHealth(self):
        payload = {
            "OS": "macOS" if self.system == "Darwin" else self.system,
            "CPU Usage": f"{self.cpuUsage}%" if self.cpuUsage is not None else "N/A",
            "Memory Usage": f"{self.memUsage.percent}%" if self.memUsage else "N/A",
            "Swap Usage": f"{self.swapUsage.percent}%" if self.swapUsage else "N/A",
            "Disk usage": f"{self.diskUsage.percent}%" if self.diskUsage else "N/A",
            "Battery": f"{self.batteryHealth.percent}%, {'Charging' if self.batteryHealth.power_plugged else 'Not plugged in'}" if self.batteryHealth is not None else "No battery detected on this system"        }
        return payload

    def checkSpecs(self):
        payload = {
            "CPU name": self.cpuModel if self.cpuModel else "N/A",
            "CPU Frequency": {
                "Current": f"{self.cpuFreq.current} GHz",
                "Min": f"{self.cpuFreq.min}",
                "Max": f"{self.cpuFreq.max}"
            } if self.cpuFreq is not None else "N/A",
            "Memory Usage": f"{self.memUsage.total / (1024 ** 3)} GB" if self.memUsage else "N/A",
            "Swap Usage": f"{self.swapUsage.total / (1024 ** 3)} GB" if self.swapUsage else "N/A",
            "Disk usage": f"{self.diskUsage.total / (1024 ** 3)} GB" if self.diskUsage else "N/A",
        }
        return payload

    def connectivityCheck(self):
        payload = {
            "Network connectivity": f"Successful connection to {self.dns}:{self.port}" if self.connectivity else f"Connection failure to {self.dns}:{self.port}",
            "Bluetooth connectivity": f"Bluetooth is {"UP" if self.checkBT() else "DOWN"}"
        }
        return payload

def healthCheck():
    """This function checks the health of the system, e.g. CPU usage, Mem usage, battery health..."""
    print("Performing health check...")
    health = SystemHealthCheck()
    return json.dumps(health.checkHealth())

def systemSpecs():
    """This function checks the specifications of the system, e.g. OS, CPU model, Mem size..."""
    print("Performing system specification check...")
    specs = SystemHealthCheck()
    return json.dumps(specs.checkSpecs())

def connectivityCheck():
    """This function reports the connectivity of the current computer"""
    print("Performing connectivity check...")
    connection = SystemHealthCheck()
    return json.dumps(connection.connectivityCheck())

def fullCheck():
    """This function reports all information. ONLY call this function when the user explicitly mentions"""
    print("Performing full check on system...")
    payload = {
        "health":healthCheck(),
        "system specifications":systemSpecs(),
        "connectivity":connectivityCheck()
    }
    return payload
