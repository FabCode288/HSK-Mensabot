#pragma once

#include <vector>
#include <string>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace mensabot_hardware
{

class MensabotHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(MensabotHardware)

  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  // externe Steuerung
  void set_estop(bool value);
  bool is_connected() const;

private:

  // Serial
  int serial_fd_;
  std::string port_ = "/dev/arduino";

  // States
  bool connected_ = false;
  bool ready_ = false;
  bool active_ = false;
  bool estop_ = false;
  bool estop_sent_ = false;

  // Timing
  rclcpp::Time last_msg_time_;
  rclcpp::Time last_send_time_;
  bool timing_initialized_ = false;
  double heartbeat_timeout_ = 1.0;
  double send_period_ = 0.2; // 5 Hz

  // Interfaces
  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;
  std::vector<double> hw_commands_;

  // Helper
  void send_string(const std::string & msg);
  std::string read_line();
};

}  // namespace mensabot_hardware