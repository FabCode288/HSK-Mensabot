# Network

The **HSK-Mensabot** uses a dedicated local Ethernet network to connect all communication-critical hardware components. A central router provides the network infrastructure and enables reliable communication between the robot, the laser scanners and the development computer.

The Raspberry Pi and both SICK NanoScan3 laser scanners are connected to the router via Ethernet. The development computer can access the network either through a wired Ethernet connection or wirelessly via Wi-Fi, allowing software development, monitoring and maintenance without modifying the robot hardware.

---

# 1. Network Topology

The following figure illustrates the network structure of the HSK-Mensabot.

<p align="center">
  <img src="/docs/images/network_plan.png" width="700">
</p>

---

# 2. IP Address Assignment

To ensure reliable communication, all permanent network devices use static IP addresses.

| Device | IP Address |
|---------|------------|
| Router | `192.168.0.1` |
| Raspberry Pi 5 | `192.168.0.100` |
| NanoScan3 Rear | `192.168.0.10` |
| NanoScan3 Front | `192.168.0.11` |
| Development PC | `192.168.0.2` *(variable)* |

Using static IP addresses eliminates address changes after reboot and simplifies communication with the robot hardware during development and operation.

---

# Related Documentation

- **[Hardware](../hardware/)**
- **[LiDAR Documentation](../hardware/lidars/)**
- **[Communication](../communication/)**
- **[Installation](../installation/)**