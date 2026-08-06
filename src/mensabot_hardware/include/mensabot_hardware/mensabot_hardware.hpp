/**
 * @file mensabot_hardware.hpp
 * @brief Declaration of the Mensabot ros2_control hardware interface.
 *
 * Defines the communication protocol, packet structures and the
 * MensabotHardware class implementing the ros2_control
 * hardware_interface::SystemInterface.
 */

#ifndef MENSABOT_HARDWARE__MENSABOT_HARDWARE_HPP_
#define MENSABOT_HARDWARE__MENSABOT_HARDWARE_HPP_

#include <atomic>
#include <cstdint>
#include <string>
#include <vector>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

#include "rclcpp/macros.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include "std_msgs/msg/bool.hpp"

// ============================================================================
// COMMUNICATION PROTOCOL
// ============================================================================

#pragma pack(push, 1)

struct Packet
{
  uint8_t header1;
  uint8_t header2;

  uint8_t type;

  int16_t value1;
  int16_t value2;

  uint16_t checksum;
};

#pragma pack(pop)

static_assert(sizeof(Packet) == 9, "Packet size invalid");

union PacketBuffer
{
  Packet packet;
  uint8_t bytes[sizeof(Packet)];
};

enum PacketType : uint8_t
{
  PKT_PING  = 1,
  PKT_READY = 2,
  PKT_HB    = 3,

  PKT_CMD   = 10,

  PKT_ESTOP = 20,
  PKT_RESET = 21
};

// ============================================================================
// HARDWARE INTERFACE
// ============================================================================

namespace mensabot_hardware
{

/**
 * @brief Hardware interface implementation for the Mensabot platform.
 */

/**
 * @brief ros2_control hardware interface for the Mensabot platform.
 *
 * This class provides the connection between the ROS 2 control framework
 * and the Arduino-based motor controller. It manages serial communication,
 * controller state transitions, heartbeat monitoring and command exchange.
 */
class MensabotHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(MensabotHardware)

  /**
   * @brief Initialize the hardware interface.
   */
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  /**
   * @brief Export wheel state interfaces.
   */
  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override;

  /**
   * @brief Export wheel command interfaces.
   */
  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override;

  /**
   * @brief Activate the hardware interface.
   */
  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  /**
   * @brief Deactivate the hardware interface.
   */
  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  /**
   * @brief Read data from the hardware interface.
   */
  hardware_interface::return_type read(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

  /**
   * @brief Write commands to the hardware interface.
   */
  hardware_interface::return_type write(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

private:

  // ==========================================================================
  // SERIAL COMMUNICATION
  // ==========================================================================

  int serial_fd_;

  std::string port_ = "/dev/arduino";

  PacketBuffer rx_buffer_;

  size_t rx_index_ = 0;

  /**
   * @brief Send a communication packet.
   */
  void send_packet(
    uint8_t type,
    int16_t value1 = 0,
    int16_t value2 = 0);

  /**
   * @brief Read a packet from the serial interface.
   */
  bool read_packet(Packet & packet);

  /**
   * @brief Calculate the packet checksum.
   */
  uint16_t calculate_checksum(
    const Packet & packet);

  // ==========================================================================
  // ROS COMMUNICATION
  // ==========================================================================

  rclcpp::Node::SharedPtr node_;

  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr estop_sub_;

  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr connected_pub_;

  // ==========================================================================
  // HARDWARE DATA
  // ==========================================================================

  std::vector<double> hw_positions_;

  std::vector<double> hw_velocities_;

  std::vector<double> hw_commands_;

  // ==========================================================================
  // STATE FLAGS
  // ==========================================================================

  bool connected_ = false;

  bool ready_ = false;

  bool active_ = false;

  std::atomic<bool> estop_{false};

  bool estop_sent_ = false;

  // ==========================================================================
  // TIMING
  // ==========================================================================

  rclcpp::Time last_msg_time_;

  rclcpp::Time last_send_time_;

  bool timing_initialized_ = false;

  double heartbeat_timeout_ = 1.0;

  double send_period_ = 0.02;  // 50 Hz
};

}  // namespace mensabot_hardware

#endif  // MENSABOT_HARDWARE__MENSABOT_HARDWARE_HPP_