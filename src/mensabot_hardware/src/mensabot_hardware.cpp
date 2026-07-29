/**
 * @file mensabot_hardware.cpp
 * @brief ROS 2 hardware interface for the Mensabot platform.
 *
 * This file implements the ros2_control SystemInterface used to connect the
 * ROS 2 control framework with the Arduino-based motor controller via a
 * serial communication interface.
 *
 * Besides transmitting wheel velocity commands, the hardware interface
 * manages the communication state machine, heartbeat monitoring, emergency
 * stop handling and packet-based data exchange.
 */

#include "mensabot_hardware/mensabot_hardware.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstring>
#include <cmath>
#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

#include "std_msgs/msg/bool.hpp"

namespace mensabot_hardware
{
  /**
  * @brief Hardware interface implementation for the Mensabot platform.
  */

hardware_interface::CallbackReturn MensabotHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  /**
  * @brief Initialize the hardware interface.
  *
  * Creates the internal ROS node, initializes publishers and subscribers,
  * configures the serial interface and prepares all internal state variables.
  *
  * @param info Hardware information provided by ros2_control.
  *
  * @return CallbackReturn::SUCCESS on successful initialization,
  *         otherwise CallbackReturn::ERROR.
  */
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  hw_positions_ = {0.0, 0.0};
  hw_velocities_ = {0.0, 0.0};
  hw_commands_ = {0.0, 0.0};

  // ================= ROS Communication NODE =================

  node_ = std::make_shared<rclcpp::Node>("mensabot_hardware_node");

  estop_sub_ =
    node_->create_subscription<std_msgs::msg::Bool>(
      "/safety/estop",
      10,
      [this](const std_msgs::msg::Bool::SharedPtr msg)
      {
        estop_ = msg->data;
    });

  connected_pub_ =
    node_->create_publisher<std_msgs::msg::Bool>(
      "/hardware/connected",
      10);

  // ================= SERIAL =================

  // Serial open NON BLOCKING
  serial_fd_ = open(port_.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);

  if (serial_fd_ < 0) {
    perror("Serial open failed");
    return hardware_interface::CallbackReturn::ERROR;
  }

  usleep(3000000);

  struct termios tty;
  memset(&tty, 0, sizeof tty);

  tcgetattr(serial_fd_, &tty);
  cfmakeraw(&tty);

  cfsetospeed(&tty, B115200);
  cfsetispeed(&tty, B115200);

  tty.c_cflag |= (CLOCAL | CREAD);
  tty.c_cflag |= CS8;
  tty.c_cflag &= ~PARENB;
  tty.c_cflag &= ~CSTOPB;

  // NON BLOCKING SERIAL
  tty.c_cc[VMIN] = 0;
  tty.c_cc[VTIME] = 0;

  tcsetattr(serial_fd_, TCSANOW, &tty);

  connected_ = false;
  ready_ = false;
  active_ = false;

  return hardware_interface::CallbackReturn::SUCCESS;
}

// ================= INTERFACES =================

std::vector<hardware_interface::StateInterface>
MensabotHardware::export_state_interfaces()
{
  /**
  * @brief Export the robot state interfaces.
  *
  * Provides position and velocity state interfaces for both drive wheels.
  *
  * @return Vector containing all exported state interfaces.
  */

  std::vector<hardware_interface::StateInterface> interfaces;

  interfaces.emplace_back(
    info_.joints[0].name,
    hardware_interface::HW_IF_POSITION,
    &hw_positions_[0]);

  interfaces.emplace_back(
    info_.joints[0].name,
    hardware_interface::HW_IF_VELOCITY,
    &hw_velocities_[0]);

  interfaces.emplace_back(
    info_.joints[1].name,
    hardware_interface::HW_IF_POSITION,
    &hw_positions_[1]);

  interfaces.emplace_back(
    info_.joints[1].name,
    hardware_interface::HW_IF_VELOCITY,
    &hw_velocities_[1]);

  return interfaces;
}

std::vector<hardware_interface::CommandInterface>
MensabotHardware::export_command_interfaces()
{
  /**
  * @brief Export the robot command interfaces.
  *
  * Provides velocity command interfaces for both drive wheels.
  *
  * @return Vector containing all exported command interfaces.
  */

  std::vector<hardware_interface::CommandInterface> interfaces;

  interfaces.emplace_back(
    info_.joints[0].name,
    hardware_interface::HW_IF_VELOCITY,
    &hw_commands_[0]);

  interfaces.emplace_back(
    info_.joints[1].name,
    hardware_interface::HW_IF_VELOCITY,
    &hw_commands_[1]);

  return interfaces;
}

// ================= ACTIVATE =================

hardware_interface::CallbackReturn MensabotHardware::on_activate(
  const rclcpp_lifecycle::State &)
{
  /**
  * @brief Activate the hardware interface.
  *
  * Called when the controller manager activates the hardware component.
  *
  * @param State Current lifecycle state.
  *
  * @return CallbackReturn::SUCCESS.
  */

  RCLCPP_INFO(
    rclcpp::get_logger("MensabotHardware"),
    "Hardware Interface ACTIVATED");

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn MensabotHardware::on_deactivate(
  const rclcpp_lifecycle::State &)
{
  /**
  * @brief Deactivate the hardware interface.
  *
  * Closes the serial connection and releases hardware resources.
  *
  * @param State Current lifecycle state.
  *
  * @return CallbackReturn::SUCCESS.
  */

  close(serial_fd_);

  RCLCPP_INFO(
    rclcpp::get_logger("MensabotHardware"),
    "Hardware Interface DEACTIVATED");

  return hardware_interface::CallbackReturn::SUCCESS;
}

// ================= READ =================

hardware_interface::return_type MensabotHardware::read(
  const rclcpp::Time & time,
  const rclcpp::Duration & period)
{
  /**
  * @brief Read data from the hardware interface.
  *
  * Processes incoming serial packets, updates the communication state,
  * monitors heartbeat timeouts and updates the wheel state information.
  *
  * During simulation of the hardware communication, wheel positions are
  * estimated from the commanded wheel velocities.
  *
  * @param time Current ROS time.
  * @param period Control period.
  *
  * @return hardware_interface::return_type::OK.
  */
  // ROS CALLBACKS
  rclcpp::spin_some(node_);

  // Publish connected state
  std_msgs::msg::Bool connected_msg;
  connected_msg.data = connected_;
  connected_pub_->publish(connected_msg);

  // Timing initialisieren mit derselben Clock
  if (!timing_initialized_) {

    last_msg_time_ = time;
    last_send_time_ = time;

    timing_initialized_ = true;

    return hardware_interface::return_type::OK;
  }

  Packet packet;
  if (read_packet(packet)) {

    //RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "RX Type=%d V1=%d V2=%d", packet.type, packet.value1, packet.value2);

    // READY
    if (packet.type == PKT_READY) {
      last_msg_time_ = time;

      if (!connected_) {

        RCLCPP_INFO(
          rclcpp::get_logger("MensabotHardware"),
          "STATE -> READY");
      }

      connected_ = true;
      ready_ = true;
    }

    // HEARTBEAT
    else if (packet.type == PKT_HB) {

      last_msg_time_ = time;

      //RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"),"Heartbeat received");
    }
  }

  // TIMEOUT
  if ((time - last_msg_time_).seconds() > heartbeat_timeout_) {

    if (connected_) {

      RCLCPP_WARN(
        rclcpp::get_logger("MensabotHardware"),
        "Heartbeat timeout");

    }

    connected_ = false;
    ready_ = false;
    active_ = false;
  }

  // Estimate wheel positions from commanded velocities because the current
  // hardware does not provide encoder feedback.
  if (active_ && connected_) {

    hw_positions_[0] += hw_commands_[0] * period.seconds();
    hw_positions_[1] += hw_commands_[1] * period.seconds();

    hw_velocities_[0] = hw_commands_[0];
    hw_velocities_[1] = hw_commands_[1];

  } else {

    hw_velocities_[0] = 0.0;
    hw_velocities_[1] = 0.0;
  }

  return hardware_interface::return_type::OK;
}

// ================= WRITE =================

hardware_interface::return_type MensabotHardware::write(
  const rclcpp::Time & time,
  const rclcpp::Duration &)
{
  /**
  * @brief Send commands to the motor controller.
  *
  * Implements the communication state machine by handling connection
  * establishment, emergency stop commands, reset requests and velocity
  * transmission.
  *
  * Velocity commands are converted into the fixed-point packet format before
  * being transmitted via the serial interface.
  *
  * @param time Current ROS time.
  * @param period Control period.
  *
  * @return hardware_interface::return_type::OK.
  */
  // RATE LIMIT
  if ((time - last_send_time_).seconds() < send_period_) {
    return hardware_interface::return_type::OK;
  }

  last_send_time_ = time;

  // WAITING -> PING
  if (!connected_) {

    send_packet(PKT_PING);

    return hardware_interface::return_type::OK;
  }

  // ESTOP
  if (estop_) {

    send_packet(PKT_ESTOP);

    // Nur einmal loggen solange ESTOP aktiv bleibt
    if (!estop_sent_) {

      RCLCPP_WARN(
        rclcpp::get_logger("MensabotHardware"),
        "ESTOP ACTIVE");
    }

    estop_sent_ = true;
    active_ = false;

    return hardware_interface::return_type::OK;
  }

  // RESET
  if (estop_sent_ && !estop_) {

    send_packet(PKT_RESET);

    estop_sent_ = false;
    ready_ = false;

    RCLCPP_INFO(
      rclcpp::get_logger("MensabotHardware"),
      "ESTOP RESET");

    return hardware_interface::return_type::OK;
  }

  // READY -> ACTIVE
  if (ready_ && !active_) {
    active_ = true;
  }

  // ACTIVE -> CMD
  if (active_) {

    int16_t left_cmd = static_cast<int16_t>(std::round(hw_commands_[0] * 100.0));
    int16_t right_cmd = static_cast<int16_t>(std::round(hw_commands_[1] * 100.0));

    // ================= BUILD PAYLOAD =================

    send_packet(PKT_CMD, left_cmd, right_cmd);
  }

  return hardware_interface::return_type::OK;
}

// ================= HELPERS =================
uint16_t MensabotHardware::calculate_checksum(
  const Packet& packet)
{
  /**
  * @brief Calculate the packet checksum.
  *
  * Generates the checksum used for packet integrity verification.
  *
  * @param packet Packet used for checksum calculation.
  *
  * @return Calculated checksum.
  */

  return static_cast<uint16_t>(
    packet.type ^
    packet.value1 ^
    packet.value2);
}

void MensabotHardware::send_packet(
  uint8_t type,
  int16_t value1,
  int16_t value2)
{
  /**
  * @brief Build and transmit a communication packet.
  *
  * Creates a packet with header, payload and checksum before sending it over
  * the serial interface.
  *
  * @param type Packet type.
  * @param value1 First payload value.
  * @param value2 Second payload value.
  */

  PacketBuffer tx;

  tx.packet.header1 = 0xAA;
  tx.packet.header2 = 0x55;

  tx.packet.type = type;

  tx.packet.value1 = value1;
  tx.packet.value2 = value2;

  tx.packet.checksum =
    calculate_checksum(tx.packet);

  ::write(
    serial_fd_,
    tx.bytes,
    sizeof(tx.bytes));

  //RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "TX Type=%d V1=%d V2=%d", type, value1, value2);
}

bool MensabotHardware::read_packet(
  Packet& packet)
{
  /**
  * @brief Receive and validate a communication packet.
  *
  * Reads incoming serial data byte by byte, reconstructs complete packets and
  * validates their checksum before returning the received packet.
  *
  * @param packet Output packet.
  *
  * @return True if a valid packet was received, otherwise false.
  */

  uint8_t byte;

  while (::read(serial_fd_, &byte, 1) > 0)
  {
    switch (rx_index_)
    {
      case 0:

        if (byte != 0xAA)
        {
          continue;
        }

        rx_buffer_.bytes[rx_index_++] = byte;
        break;

      case 1:

        if (byte != 0x55)
        {
          rx_index_ = 0;
          continue;
        }

        rx_buffer_.bytes[rx_index_++] = byte;
        break;

      default:

        rx_buffer_.bytes[rx_index_++] = byte;

        if (rx_index_ >= sizeof(Packet))
        {
          rx_index_ = 0;

          uint16_t checksum =
            calculate_checksum(
              rx_buffer_.packet);

          if (checksum !=
              rx_buffer_.packet.checksum)
          {
            return false;
          }

          packet = rx_buffer_.packet;

          return true;
        }

        break;
    }
  }

  return false;
}

}  // namespace mensabot_hardware

PLUGINLIB_EXPORT_CLASS(
  mensabot_hardware::MensabotHardware,
  hardware_interface::SystemInterface)