# lldp_and_signal
This script will automatically detect the vendor and execute the necessary commands.

Work logic:
1. First, take the com_table_sample.xlsx file and fill it in. It is important to take into account the interface names,
since the script will read data from the switches/routers, and if the interface name does not match, it will display "Mistake".
2. After filling, save the file with the name com_table.xlsx
3. Next, in ip.txt, specify the IP addresses from which you need to collect data.
4. In .env, specify the login and password. If the password does not match on one or more devices, the script
will offer to write the logpass manually, or skip this IP address.
5. Wait for the script to execute. The final table will be saved in the data directory.

It is necessary to keep in mind that LLDP check works for all 4 vendors: Huawei (DataCenter switches), Cisco (Nexus Switches), B4COM 4xxx-2xxx switches.
TX/RX signal check works only for Huawei (DataCenter switches) and B4COM 4xxx switches.

RX/TX comparison is performed as follows: it takes the current TX/RX value from the switch/router and compares it with the range from -4 to 4.
If between this range = GOOD, if not = BAD, if -, --, -40.00 = No Signal
If the value needs to be changed, it is necessary to change the values ​​to the required ones in classes/excel_handler.py in line 101.

Later will update RX/TX siganl check to be able collect from Cisco and B4COM 2xxx switches.
