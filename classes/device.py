from netmiko import ConnectHandler

class Device:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.vendor = None
        self.connection = None

    def connect(self):
        try:
            self.connection = ConnectHandler(
                device_type='autodetect',
                host=self.ip,
                username=self.username,
                password=self.password,
                global_delay_factor=2,
                read_timeout_override=100, #important command
                timeout=30,
                fast_cli=False
            )
            return True
        except Exception as e:
            if "Authentication failed" in str(e):
                print(f"Authentication failed for {self.ip}.")
            else:
                print(f"Failed to connect to {self.ip}: {str(e)}")
            return False

    def detect_vendor(self):
        commands = ["show version", "show ver | i BCOM", "dis version | i HUAWEI"]
        output = None

        for command in commands:
            output = self.connection.send_command(command)
            if 'Huawei' in output:
                self.vendor = 'Huawei'
                break
            elif 'Cisco' in output:
                self.vendor = 'Cisco'
                break
            elif 'BCOM' in output:
                self.vendor = 'B4COM'
                break
            elif 'B4TECH' in output:
                self.vendor = 'B4TECH'
                break
        else:
            self.vendor = 'Unknown'  # If no match is found after all commands

        print(f"Vendor detected: {self.vendor}")  # Debug print to check the result

    def execute_commands(self, commands):
        if not self.connection:
            raise Exception("No active connection to execute commands.")
        results = {}
        for command in commands:
            results[command] = self.connection.send_command(command)
        return results

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
