import psutil

class SystemHealthCheck:
    def __init__(self):
        self.cpuUsage = psutil.cpu_percent(interval=0.1)
        self.memUsage = psutil.virtual_memory()
        self.diskUsage = psutil.disk_usage("/")
        self.swapUsage = psutil.swap_memory()
        self.batteryHealth = psutil.sensors_battery()

    def checkHealth(self):
        payload = {
            "CPU Usage": f"{self.cpuUsage}%" if self.cpuUsage is not None else "N/A",
            "Memory Usage": f"{self.memUsage.percent}%" if self.memUsage else "N/A",
            "Swap Usage": f"{self.swapUsage.percent}%" if self.swapUsage else "N/A",
            "Disk usage": f"{self.diskUsage.percent}%" if self.diskUsage else "N/A",
            "Battery": f"{self.batteryHealth.percent}%, {'Charging' if self.batteryHealth.power_plugged else 'Not plugged in'}" if self.batteryHealth is not None else "No battery detected on this system"
        }
        return payload

def healthCheck():
    """This function checks the health of the system, e.g. CPU usage, Mem usage, battery health..."""
    print("Performing health check...")
    health = SystemHealthCheck()
    return health.checkHealth()
