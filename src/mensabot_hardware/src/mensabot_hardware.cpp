#include "mensabot_hardware/mensabot_hardware.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstring>
#include <sstream>

#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

namespace mensabot_hardware
{

hardware_interface::CallbackReturn MensabotHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  hw_positions_ = {0.0, 0.0};
  hw_velocities_ = {0.0, 0.0};
  hw_commands_ = {0.0, 0.0};

  // Serial open
  serial_fd_ = open(port_.c_str(), O_RDWR | O_NOCTTY);

  if (serial_fd_ < 0) {
    perror("Serial open failed");
    return hardware_interface::CallbackReturn::ERROR;
  }

  struct termios tty;
  memset(&tty, 0, sizeof tty);

  tcgetattr(serial_fd_, &tty);

  cfsetospeed(&tty, B115200);
  cfsetispeed(&tty, B115200);

  tty.c_cflag |= (CLOCAL | CREAD);
  tty.c_cflag |= CS8;
  tty.c_cflag &= ~PARENB;
  tty.c_cflag &= ~CSTOPB;

  tcsetattr(serial_fd_, TCSANOW, &tty);

  connected_ = false;
  ready_ = false;
  active_ = false;

  last_msg_time_ = rclcpp::Clock().now();

  return hardware_interface::CallbackReturn::SUCCESS;
}

// ================= INTERFACES =================

std::vector<hardware_interface::StateInterface>
MensabotHardware::export_state_interfaces()
{
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
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Activated");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn MensabotHardware::on_deactivate(
  const rclcpp_lifecycle::State &)
{
  close(serial_fd_);
  return hardware_interface::CallbackReturn::SUCCESS;
}

// ================= READ =================

hardware_interface::return_type MensabotHardware::read(
  const rclcpp::Time & time, const rclcpp::Duration & period)
{
  std::string line = read_line();

  if (!line.empty()) {
    last_msg_time_ = time;

    if (line == "READY") {
      connected_ = true;
      ready_ = true;
    }

    if (line == "HB") {
      connected_ = true;
    }
  }

  // Timeout
  if ((time - last_msg_time_).seconds() > heartbeat_timeout_) {
    connected_ = false;
    ready_ = false;
    active_ = false;
  }

  // Fake odom nur wenn aktiv
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
  const rclcpp::Time &, const rclcpp::Duration &)
{
  // NICHT verbunden → nur PING
  if (!connected_) {
    send_string("PING");
    return hardware_interface::return_type::OK;
  }

  // ESTOP
  if (estop_) {
    send_string("ESTOP");
    estop_sent_ = true;
    active_ = false;
    return hardware_interface::return_type::OK;
  }

  // RESET nach ESTOP
  if (estop_sent_ && !estop_) {
    send_string("RESET");
    estop_sent_ = false;
    ready_ = false;
    return hardware_interface::return_type::OK;
  }

  // READY → ACTIVE
  if (ready_) {
    active_ = true;
  }

  // wenn nicht aktiv → nichts senden
  if (!active_) {
    return hardware_interface::return_type::OK;
  }

  // CMD senden
  std::stringstream ss;
  ss << "CMD," << hw_commands_[0] << "," << hw_commands_[1];
  send_string(ss.str());

  return hardware_interface::return_type::OK;
}

// ================= HELPERS =================

void MensabotHardware::send_string(const std::string & msg)
{
  std::string m = msg + "\n";
  ::write(serial_fd_, m.c_str(), m.size());
}

std::string MensabotHardware::read_line()
{
  char buffer[256];
  int n = ::read(serial_fd_, buffer, sizeof(buffer));

  if (n > 0) {
    return std::string(buffer, n);
  }
  return "";
}

// ================= FLAGS =================

void MensabotHardware::set_estop(bool value)
{
  estop_ = value;
}

bool MensabotHardware::is_connected() const
{
  return connected_;
}

}  // namespace mensabot_hardware

PLUGINLIB_EXPORT_CLASS(
  mensabot_hardware::MensabotHardware,
  hardware_interface::SystemInterface)