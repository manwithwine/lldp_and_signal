import os
from dotenv import load_dotenv

from classes.device import Device
from classes.parser import LogParser
from classes.excel_handler import ExcelHandler
from classes.cleanup_output import OutputCleaner
from classes.cleanup_signal_output import SignalOutputCleaner
from classes.parser_signal import SignalLogParser


load_dotenv()  # Load environment variables from a .env file


def read_ip_addresses(file_path):
    with open(file_path, "r") as file:
        return file.readlines()


def write_cleaned_logs_to_file(cleaned_logs, filename="logs/cleaned_logs.txt"):
    """Write cleaned logs to a text file."""
    with open(filename, "w") as file:
        for vendor, devices in cleaned_logs.items():
            file.write(f"Vendor: {vendor}\n")
            for ip, logs in devices.items():
                file.write(f"Device IP: {ip}\n")
                file.write(logs)
                file.write("\n" + "-" * 40 + "\n")
    print(f"Cleaned logs written to {filename}")


def write_signal_logs_to_file(signal_logs, filename="logs/signal_logs.txt"):
    """Write signal logs to a text file."""
    with open(filename, "w") as file:
        for ip, raw_log in signal_logs.items():
            # device_vendor = "Huawei"  # Replace with dynamic vendor detection if needed
            file.write(f"Device IP: {ip}\n")
            cleaned_log = SignalOutputCleaner.cleanup_signal_output(ip, raw_log)
            file.write(f"{cleaned_log}\n")
            file.write("\n" + "-" * 40 + "\n")
    print(f"Signal logs written to {filename}")


def main():
    # Read IP addresses from the file
    ip_addresses = read_ip_addresses("ip.txt")
    if not ip_addresses:
        print("No IP addresses found in ip.txt")
        return

    # Initialize the Excel handler
    excel_handler = ExcelHandler("com_table.xlsx")
    all_logs = {}
    signal_logs = {}

    # Retrieve credentials from environment variables
    default_username = os.getenv("DEVICE_USERNAME", "login")
    default_password = os.getenv("DEVICE_PASSWORD", "password")

    # Collect and clean logs for each device
    for ip in ip_addresses:
        ip = ip.strip()  # Strip newline and spaces
        if not ip:
            continue

        print(f"Processing device with IP: {ip}")
        device = Device(ip, username=default_username, password=default_password)

        while True:
            # Establish connection and detect vendor
            if device.connect():
                print(f"Successfully connected to {ip}. Detecting vendor...")

                device.detect_vendor()

                # Define commands for each vendor
                commands = {
                    "Huawei": ["screen-length 0 temporary", "display sysname", "display lldp neighbor brief", "display interface transceiver brief"],
                    "Cisco": ["terminal length 0", "show hostname", "show lldp neighbors", "sh int transceiver det | exclude present"],
                    "B4COM": ["terminal length 0", "show hostname", "show lldp neighbors brief | include bridge", "sh int transceiver | exclude Codes"],
                    "B4TECH": ["terminal length 0", "show run | i hostname", "show lldp neigh br", "sh transceiver detail"],
                }

                # Execute the commands for the detected vendor
                if device.vendor in commands:
                    print(f"Executing commands for {device.vendor}...")
                    raw_logs = device.execute_commands(commands[device.vendor])

                    cleaned_logs = {}
                    signal_log_parts = []

                    # Process each command's output
                    for idx, (command, output) in enumerate(raw_logs.items()):
                        cleaned_output = OutputCleaner.cleanup_output(device.vendor, output)

                        # Cleaned logs: Add cleaned output of the 2nd and 3rd commands
                        if idx in {1, 2}:  # Commands 2nd and 3rd
                            cleaned_logs[command] = cleaned_output

                        # Signal logs: Add raw output of the 2nd and 4th commands
                        if idx in {1, 3}:  # Commands 2nd and 4th
                            raw_signal_log = f"{output}"
                            cleaned_signal_log = SignalOutputCleaner.cleanup_signal_output(device.vendor, raw_signal_log)
                            signal_log_parts.append(cleaned_signal_log)

                    # Store cleaned logs and signal logs separately per device and vendor
                    if device.vendor not in all_logs:
                        all_logs[device.vendor] = {}
                    all_logs[device.vendor][ip] = "\n".join(cleaned_logs.values())

                    signal_logs[ip] = "\n".join(signal_log_parts)

                    print(f"Logs for {device.vendor} collected and cleaned.")

                # Disconnect the device after processing
                device.disconnect()
                print(f"Disconnected from {ip}")
                break
            else:
                print(f"Failed to connect to device with IP: {ip}.")
                choice = input("Enter new credentials (y) or skip (s): ").strip().lower()
                if choice == "y":
                    device.username = input("Username: ").strip()
                    device.password = input("Password: ").strip()
                elif choice == "s":
                    break

    if not all_logs:
        print("No logs were collected.")
        return

    # Write cleaned logs and signal logs to text files
    write_cleaned_logs_to_file(all_logs)
    write_signal_logs_to_file(signal_logs)

    # Parse logs and prepare data for Excel
    parsed_data = []
    for vendor, logs in all_logs.items():
        # logs is a dictionary, so access the values (which should be strings)
        for ip, log_content in logs.items():
            # Now log_content is a string, so we can use splitlines()
            lines = log_content.splitlines()

            if vendor == "Cisco":
                parsed_data.extend(LogParser.parse_cisco_logs(lines))
            elif vendor == "Huawei":
                parsed_data.extend(LogParser.parse_huawei_logs(lines))
            elif vendor == "B4COM":
                parsed_data.extend(LogParser.parse_b4com_logs(lines))
            elif vendor == "B4TECH":
                parsed_data.extend(LogParser.parse_b4tech_logs(lines))

    if not parsed_data:
        print("No data was parsed from logs.")
        return

    # Parse logs and prepare data for Excel
    parsed_signal_data = []
    for ip, log_content in signal_logs.items():
        # Detect vendor for the current device
        vendor = None
        for device_vendor, devices in all_logs.items():
            if ip in devices:
                vendor = device_vendor
                break

        if not vendor:
            print(f"Vendor not found for IP: {ip}. Skipping signal logs parsing.")
            continue

        lines = log_content.splitlines()
        if vendor == "Huawei":
            parsed_signal_data.extend(SignalLogParser.parse_huawei_signal_logs(lines))
        elif vendor == "B4COM":
            parsed_signal_data.extend(SignalLogParser.parse_b4com_signal_logs(lines))

    # Populate Excel and compare rows
    print(f"Populating Excel file and comparing rows...")
    result_file = excel_handler.populate_and_compare(parsed_data, parsed_signal_data)
    print(f"Comparison results saved to {result_file}")



if __name__ == "__main__":
    main()