# LiDARs

The **HSK-Mensabot** uses two **SICK NanoScan3** safety laser scanners to provide 360° environmental perception and certified safety monitoring. One scanner is mounted at the front and one at the rear of the robot. Together they provide obstacle detection for autonomous navigation while simultaneously implementing the safety functions required for robot operation.

---

# 1. Hardware Overview

The robot is equipped with two identical SICK NanoScan3 safety laser scanners.

| Component | Description |
|-----------|-------------|
| Front NanoScan3 | Front environment monitoring and safety protection |
| Rear NanoScan3 | Rear environment monitoring and safety protection |

The two scanners are positioned to provide complete coverage around the robot and allow seamless transitions between forward and backward movement.

---

# 2. Technical Specifications

The most important specifications of the laser scanners are summarized below.

| Parameter | Value |
|-----------|-------|
| Manufacturer | SICK |
| Model | NanoScan3 |
| Communication | Industrial Ethernet |
| Scan Angle | 275° |
| Safety Function | Protective and warning field monitoring |
| Number of Sensors | 2 |

Detailed electrical and mechanical specifications are available in the included datasheets.

---

# 3. Mounting Position

The front and rear laser scanners are mounted close to the outer edges of the robot to maximize the monitored area while minimizing blind spots.

The scan areas overlap during robot operation, allowing continuous obstacle detection in every driving direction. This arrangement also enables different monitoring cases depending on the current driving direction and robot state.

---

# 4. Network Configuration

Both NanoScan3 scanners communicate with the Raspberry Pi through dedicated Ethernet connections using static IP addresses.

The scanner parameters, monitoring cases and communication settings are configured using the **SICK Safety Designer** software.

General network configuration of the robot is described in the **[Network Documentation](../../network/)**.

---

# 5. Safety Monitoring Cases

The NanoScan3 scanners use multiple monitoring cases consisting of protective and warning fields. Depending on the current operating mode, different monitoring cases are selected through the Raspberry Pi GPIO interface.

The following figure illustrates the monitoring fields used for forward operation.

<p align="center">
  <img src="../../images/stopfield_front.png" width="700">
</p>

The protective field immediately stops the robot when an object enters the monitored area. The surrounding warning field reduces the robot speed before the protective field is reached, enabling smooth and safe obstacle avoidance.

The monitoring cases are switched through the GPIO outputs described in the Hardware documentation and are continuously supervised by the safety system.

The protective field immediately stops the robot when an object enters the monitored area. The surrounding warning field reduces the robot speed before the protective field is reached, enabling smooth and safe obstacle avoidance.

The HSK-Mensabot uses multiple monitoring cases that are automatically selected depending on the current operating state.

| Monitoring Case | Description |
|-----------------|-------------|
| **Front** | Active during forward driving. The front protective and warning fields monitor the driving direction. |
| **Backwards** | Active during reverse driving. The rear monitoring fields provide obstacle detection while reversing. |
| **Rotate Left** | Optimized monitoring field for counterclockwise rotation of the robot. |
| **Rotate Right** | Optimized monitoring field for clockwise rotation of the robot. |
| **Standstill** | Reduced monitoring field used while the robot is stationary, maintaining obstacle detection without unnecessary field extensions. |
| **Empty** | Monitoring fields are deactivated for maintenance and commissioning purposes. This mode can only be activated manually and is not intended for normal robot operation. |

The active monitoring case is selected by the Raspberry Pi through dedicated GPIO outputs connected to the safety relay interface. This allows the monitored area to adapt dynamically to the current operating state while maintaining certified safety functionality.

---

# 6. ROS2 Integration

The NanoScan3 scanners are integrated into the ROS2 ecosystem through the official driver and publish both scan data and safety-related information.

Typical ROS interfaces include:

| Topic | Description |
|--------|-------------|
| Front scan | Front laser scan |
| Rear scan | Rear laser scan |
| Merged scan | Combined scan used by navigation |
| Output paths | Active monitoring case outputs |

The merged laser scan is used by the navigation stack for localization, mapping and path planning, while the safety outputs are evaluated by the Safety Control Node.

---

# 7. Configuration Files

The scanner configuration files used by the project are located in:

- **config/** – Scanner configuration files
- **datasheets/** – Manufacturer datasheets for the NanoScan3
- **reports/** – Verification reports generated during scanner configuration

These resources allow the complete scanner configuration to be reproduced and verified.

---

# 8. Additional Resources

The documentation includes:

- Configuration files
- Manufacturer datasheets
- Verification reports
- Images
- Official SICK documentation

---

# Related Documentation

- **[Hardware](../)**
- **[Safety](../../safety/)**
- **[Navigation](../../navigation/)**
- **[Network](../../network/)**