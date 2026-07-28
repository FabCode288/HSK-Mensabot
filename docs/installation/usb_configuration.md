# USB Device Mapping with udev (Raspberry Pi / Linux)

## Purpose

This project uses multiple USB serial devices:

- Arduino UNO (Motor Controller)
- IMU Sensor

Linux dynamically assigns serial device names such as:

/dev/ttyUSB0
/dev/ttyUSB1

The numbering can change after rebooting or reconnecting devices.
This may cause software to connect to the wrong hardware device.

To solve this problem, persistent symbolic links are created using udev.

Example:

/dev/arduino
/dev/myimu

These names stay stable even if Linux changes the internal ttyUSBX numbering.

------------------------------------------------------------
Step 1 - Connect Devices
------------------------------------------------------------

Connect all USB serial devices to the system.

Check connected USB devices:
```bash
lsusb
```
Typical output for CH340-based devices:

1a86:7523 QinHeng Electronics CH340 serial converter

------------------------------------------------------------
Step 2 - Identify Serial Devices
------------------------------------------------------------

List available serial devices:

ls /dev/ttyUSB*

Example:

/dev/ttyUSB0
/dev/ttyUSB1

------------------------------------------------------------
Step 3 - Determine Which Device is Which
------------------------------------------------------------

Use:

dmesg | tail -30

immediately after plugging in a device.

Linux will show which device was assigned:

ch341-uart converter now attached to ttyUSB0

Repeat for:
- Arduino
- IMU

------------------------------------------------------------
Step 4 - Find Unique USB Paths
------------------------------------------------------------

Use udevadm to inspect each device.

Example for IMU:

udevadm info -a -n /dev/ttyUSB0

Example for Arduino:

udevadm info -a -n /dev/ttyUSB1

Search the output for:

ID_PATH

Example:

ID_PATH=platform-xhci-hcd.0-usb-0:1:1.0

This value identifies the physical USB connection and is more robust than matching KERNELS.

Example used in this project:

IMU
ID_PATH=platform-xhci-hcd.0-usb-0:1:1.0

Arduino
ID_PATH=platform-xhci-hcd.1-usb-0:2:1.0

------------------------------------------------------------
Step 5 - Create udev Rules
------------------------------------------------------------

IMU Rule:

sudo nano /etc/udev/rules.d/myimu.rules

Content:

SUBSYSTEM=="tty", ENV{ID_PATH}=="platform-xhci-hcd.0-usb-0:1:1.0", SYMLINK+="myimu", MODE:="0666"

Arduino Rule:

sudo nano /etc/udev/rules.d/arduino.rules

Content:

SUBSYSTEM=="tty", ENV{ID_PATH}=="platform-xhci-hcd.1-usb-0:2:1.0", SYMLINK+="arduino", MODE:="0666"

------------------------------------------------------------
Step 6 - Reload udev Rules
------------------------------------------------------------

sudo udevadm control --reload-rules
sudo udevadm trigger

Reconnect both USB devices afterwards.

------------------------------------------------------------
Step 7 - Verify
------------------------------------------------------------

ls -l /dev/myimu
ls -l /dev/arduino

Expected result:

/dev/myimu -> ttyUSB0
/dev/arduino -> ttyUSB1

The target ttyUSBX numbers may change.
The symbolic names remain stable.

------------------------------------------------------------
Step 8 - Use in Software
------------------------------------------------------------

Example:

std::string imu_port = "/dev/myimu";
std::string arduino_port = "/dev/arduino";

------------------------------------------------------------
Optional - Serial Permissions
------------------------------------------------------------

To access serial devices without sudo:

sudo usermod -aG dialout $USER

Reboot afterwards:

sudo reboot

------------------------------------------------------------
Notes
------------------------------------------------------------

- This setup depends on the devices staying connected to the same USB ports.
If devices are connected to different USB ports, the ID_PATH values must be updated.

Using ID_PATH is more robust than matching KERNELS because it relies on the physical USB connection rather than the kernel device hierarchy.
- CH340-based devices often do not provide unique serial numbers,
  therefore USB path matching is used.

------------------------------------------------------------
Summary
------------------------------------------------------------

/dev/arduino -> Arduino Controller
/dev/myimu   -> IMU Sensor

This avoids issues caused by changing Linux serial device numbering.

USB Ports:
Top Left: Unused
Top Right: Unused
Bottom Left: IMU
Bottom Right: Arduino
