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

// 🔥 NEU: Rate Control Variablen
rclcpp::Time last_send_time_;
double send_period_ = 0.05; // 20 Hz

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

  // Initialisierung Sendetimer
  last_send_time_ = rclcpp::Clock().now();

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
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Activated Fabian's Mensabot Hardware");
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
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), connected_ ? "Connected" : "Not Connected");
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), active_ ? "Active" : "Not Active");

  std::string line = read_line();

  if (!line.empty()) {
    RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), line.c_str());

    if (line == "READY" || line == " READY" || line == " READY " || line == "READY "  || line == "READY\n") {
      RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Read: line = READY");
      connected_ = true;
      ready_ = true;
      last_msg_time_ = time;
    }

    if (line == "HB" || line == " HB" || line == "HB\n") {
      RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Read: line = HB");
      last_msg_time_ = time;
    }
  }

  if ((time - last_msg_time_).seconds() > heartbeat_timeout_) {
    RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Timeout Reset Heartbeat");
    connected_ = false;
    ready_ = false;
    active_ = false;
  }

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
  // Rate Limiting
  rclcpp::Time now = rclcpp::Clock().now();
  if ((now - last_send_time_).seconds() < send_period_) {
    return hardware_interface::return_type::OK;
  }
  last_send_time_ = now;

  if (!connected_) {
    send_string("PING");
    return hardware_interface::return_type::OK;
  }

  if (estop_) {
    send_string("ESTOP");
    estop_sent_ = true;
    active_ = false;
    RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "ESTOP");
    return hardware_interface::return_type::OK;
  }

  if (estop_sent_ && !estop_) {
    send_string("RESET");
    estop_sent_ = false;
    ready_ = false;
    RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "ESTOP - RESET");
    return hardware_interface::return_type::OK;
  }

  if (ready_) {
    active_ = true;
  }

  if (!active_) {
    return hardware_interface::return_type::OK;
  }

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
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Sent: %s", msg.c_str());
}

std::string MensabotHardware::read_line()
{
  char buffer[256];
  int n = ::read(serial_fd_, buffer, sizeof(buffer));

  if (n > 0) {
    return std::string(buffer, n);
  }
  RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "Failed to read line");
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