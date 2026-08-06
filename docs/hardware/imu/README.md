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

The IMU is mounted inside the robot in the centre above the driven axle. It is rigidly attached to the robot frame.

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

Additional information about the ROS2 driver can be found in the imu package:

- **[`src/imu_ros2_device`](../../../src/imu_ros2_device/)**

---

# 5. Validation

The IMU was initially validated independently from the remaining robot software before being integrated into the localization pipeline.

During commissioning, the published sensor measurements and the estimated orientation were evaluated by performing controlled rotational movements of the robot. The measured orientation was compared with the actual robot motion to verify the correct operation of the sensor and the ROS2 driver.

As expected for a MEMS-based IMU, the sensor exhibits a small, continuous orientation drift over time due to measurement noise and bias. While this drift is negligible during short-term motion, it accumulates during longer operating periods and therefore cannot be used as the sole source for robot localization.

To compensate for this behavior, the filtered IMU measurements are fused with the wheel odometry in the Extended Kalman Filter (EKF). This sensor fusion significantly improves the stability of the estimated robot pose and provides the odometry required by the localization and navigation system.

---

# 6. Additional Resources

Further information about the IMU can be found in:

- **`src/imu_ros2_device/`** – ROS2 driver package and configuration
- Manufacturer documentation: https://www.yahboom.net/study/IMU_Sensor

---

# Related Documentation

- **[Hardware](../)**
- **[Navigation](../../navigation/)**
- **[Communication](../../communication/)**
- **[Network](../../network/)**