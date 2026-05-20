#include "mensabot_hardware/mensabot_hardware.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstring>
#include <sstream>
#include <algorithm>

#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

#include "std_msgs/msg/bool.hpp"

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
  RCLCPP_INFO(
    rclcpp::get_logger("MensabotHardware"),
    "Hardware Interface ACTIVATED");

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn MensabotHardware::on_deactivate(
  const rclcpp_lifecycle::State &)
{
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

  std::string line = read_line();

  if (!line.empty()) {

    //RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "RX: %s", line.c_str());

    // READY
    if (line == "READY") {

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
    else if (line == "HB") {

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

  // Fake Odom
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
  // RATE LIMIT
  if ((time - last_send_time_).seconds() < send_period_) {
    return hardware_interface::return_type::OK;
  }

  last_send_time_ = time;

  // WAITING -> PING
  if (!connected_) {

    send_string("PING");

    return hardware_interface::return_type::OK;
  }

  // ESTOP
  if (estop_) {

    send_string("ESTOP");

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

    send_string("RESET");

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

    int left_cmd = static_cast<int>(std::round(hw_commands_[0] * 100.0));
    int right_cmd = static_cast<int>(std::round(hw_commands_[1] * 100.0));

    // ================= BUILD PAYLOAD =================

    std::stringstream ss;

    ss << "CMD,"
      << left_cmd
      << ","
      << right_cmd;

    std::string payload = ss.str();

    // ================= XOR CHECKSUM =================

    uint8_t checksum = 0;

    for (char c : payload) {

        checksum ^= static_cast<uint8_t>(c);
    }

    // ================= FINAL MESSAGE =================

    std::stringstream final_msg;

    final_msg << payload
              << ","
              << static_cast<int>(checksum);

    send_string(final_msg.str());
  }

  return hardware_interface::return_type::OK;
}

// ================= HELPERS =================

void MensabotHardware::send_string(const std::string & msg)
{
  std::string m = msg + "\n";

  ::write(serial_fd_, m.c_str(), m.size());

  //RCLCPP_INFO(rclcpp::get_logger("MensabotHardware"), "TX: %s", msg.c_str());
}

std::string MensabotHardware::read_line()
{
  static std::string rx_buffer;

  char buffer[256];

  int n = ::read(serial_fd_, buffer, sizeof(buffer));

  if (n > 0) {

    // Neue Daten anhängen
    rx_buffer.append(buffer, n);

    // Nach kompletter Zeile suchen
    size_t pos = rx_buffer.find('\n');

    if (pos != std::string::npos) {

      // Zeile extrahieren
      std::string line = rx_buffer.substr(0, pos);

      // Aus Buffer entfernen
      rx_buffer.erase(0, pos + 1);

      // \r entfernen
      line.erase(
        std::remove(line.begin(), line.end(), '\r'),
        line.end());

      return line;
    }
  }

  return "";
}

}  // namespace mensabot_hardware

PLUGINLIB_EXPORT_CLASS(
  mensabot_hardware::MensabotHardware,
  hardware_interface::SystemInterface)