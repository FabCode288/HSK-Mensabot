#include "mensabot_hardware/mensabot_hardware.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstring>
#include <cstdio>
#include <cmath>

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

  // Serial öffnen
  serial_fd_ = open("/dev/ttyACM0", O_RDWR | O_NOCTTY);

  if (serial_fd_ < 0) {
    perror("Serial open failed");
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Serial konfigurieren
  struct termios tty;
  memset(&tty, 0, sizeof tty);

  if (tcgetattr(serial_fd_, &tty) != 0) {
    perror("tcgetattr failed");
    return hardware_interface::CallbackReturn::ERROR;
  }

  cfsetospeed(&tty, B115200);
  cfsetispeed(&tty, B115200);

  tty.c_cflag |= (CLOCAL | CREAD);
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |= CS8;
  tty.c_cflag &= ~PARENB;
  tty.c_cflag &= ~CSTOPB;

  tcsetattr(serial_fd_, TCSANOW, &tty);

  // 🔥 WICHTIG: Arduino reset → kurz warten
  usleep(2000000); // 2 Sekunden

  return hardware_interface::CallbackReturn::SUCCESS;
}

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

hardware_interface::CallbackReturn MensabotHardware::on_activate(
  const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Hardware activated");

  // 🔥 Safety: initial STOP
  hw_commands_[0] = 0.0;
  hw_commands_[1] = 0.0;

  const char * stop_msg = "0.0,0.0\n";
  ::write(serial_fd_, stop_msg, strlen(stop_msg));

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn MensabotHardware::on_deactivate(
  const rclcpp_lifecycle::State &)
{
  // 🔥 STOP beim Beenden
  const char * stop_msg = "0.0,0.0\n";
  ::write(serial_fd_, stop_msg, strlen(stop_msg));

  close(serial_fd_);

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type MensabotHardware::read(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  char buffer[256];
  int n = ::read(serial_fd_, buffer, sizeof(buffer) - 1);

  if (n > 0) {
    buffer[n] = '\0'; // Null-terminieren
    std::string line(buffer);

    double t, pos_l, pos_r, vel_l, vel_r;

    if (sscanf(line.c_str(), "%lf,%lf,%lf,%lf,%lf",
               &t, &pos_l, &pos_r, &vel_l, &vel_r) == 5)
    {
      hw_positions_[0] = pos_l;
      hw_positions_[1] = pos_r;
      hw_velocities_[0] = vel_l;
      hw_velocities_[1] = vel_r;
    }
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type MensabotHardware::write(
  const rclcpp::Time &, const rclcpp::Duration &)
{
  // 🔥 Safety: NaN/Inf verhindern
  if (!std::isfinite(hw_commands_[0]) || !std::isfinite(hw_commands_[1])) {
    hw_commands_[0] = 0.0;
    hw_commands_[1] = 0.0;
  }

  char msg[128];
  snprintf(msg, sizeof(msg), "%.3f,%.3f\n",
           hw_commands_[0], hw_commands_[1]);

  ::write(serial_fd_, msg, strlen(msg));

  return hardware_interface::return_type::OK;
}

}  // namespace mensabot_hardware

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  mensabot_hardware::MensabotHardware,
  hardware_interface::SystemInterface)