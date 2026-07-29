# IMU

The **HSK-Mensabot** uses a **Yahboom Inertial Measurement Unit (IMU)** to provide linear acceleration and angular velocity measurements for state estimation. The IMU complements the wheel odometry by providing orientation information that is fused within the robot localization framework. Since the robot does not use wheel encoders, the IMU plays an important role in achieving a stable pose estimation.

---

# 1. Hardware Overview

The robot is equipped with a single Yahboom IMU connected directly to the Raspberry Pi.

| Component | Description |
|-----------|-------------|
| Yahboom IMU | Inertial Measurement Unit for state estimation |

The IMU provides acceleration and angular velocity measurements that are processed by the robot localization pipeline.

---

# 2. Technical Specifications

The most important characteristics of the IMU are summarized below.

| Parameter | Value |
|-----------|-------|
| Manufacturer | Yahboom |
| Sensor Type | Inertial Measurement Unit |
| Communication | USB |
| Measured Values | Linear acceleration, angular velocity |
| Number of Sensors | 1 |

Further technical information is available from the manufacturer documentation and the ROS2 driver package.

---

# 3. Mounting Position

The IMU is mounted inside the robot above the driven axle and close to the geometric center of the platform. It is installed inside the router enclosure and rigidly attached to the robot frame.

This mounting position minimizes the influence of rotational offsets and allows the measured accelerations and angular velocities to represent the robot motion as accurately as possible.

---

# 4. ROS2 Integration

The IMU communicates with the Raspberry Pi via a USB serial interface and is integrated into ROS2 using the **imu_ros2_device** package.

The driver continuously publishes both raw and processed sensor measurements.

| Topic | Description |
|--------|-------------|
| `/imu/data_raw` | Raw accelerometer and gyroscope measurements |
| `/imu/data` | Filtered IMU data including orientation |

The raw sensor measurements are processed using the **Madgwick filter**, which estimates the robot orientation from the measured accelerations and angular velocities. The resulting orientation data is subsequently fused together with the wheel odometry inside the **Extended Kalman Filter (EKF)** to generate the robot odometry used for localization and autonomous navigation.

Additional information about the ROS2 driver can be found in the repository:

- **[`src/imu_ros2_device`](../../../src/imu_ros2_device/)**

---

# 5. Validation

The IMU was initially tested independently from the remaining robot software.

During commissioning, the published sensor measurements and the estimated orientation were verified by performing controlled rotational movements of the robot and comparing the reported orientation with the actual motion.

After successful verification, the IMU was integrated into the EKF-based sensor fusion pipeline and used as part of the complete localization system.

---

# 6. Additional Resources

Further information about the IMU can be found in:

- **`src/imu_ros2_device/`** – ROS2 driver package and configuration
- Manufacturer documentation

---

# Related Documentation

- **[Hardware](../)**
- **[Navigation](../../navigation/)**
- **[Communication](../../communication/)**
- **[Network](../../network/)**