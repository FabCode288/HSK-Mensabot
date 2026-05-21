#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from nav2_msgs.msg import SpeedLimit

# SICK Safety Scanner Message
from sick_safetyscanners2_interfaces.msg import OutputPaths


class SafetyControlNode(Node):

    def __init__(self):
        super().__init__('safety_control_node')

        # ======================================================
        # PARAMETERS
        # ======================================================

        self.declare_parameter(
            'simulation',
            False
        )

        self.simulation_mode = self.get_parameter(
            'simulation'
        ).get_parameter_value().bool_value

        # ======================================================
        # GPIO CONFIG
        # ======================================================

        self.gpio_available = False

        if not self.simulation_mode:

            try:

                import gpiod
                from gpiod.line import Direction

                self.gpiod = gpiod
                self.Direction = Direction

                self.gpio_chip_path = "/dev/gpiochip4"
                self.gpio_line_number = 17

                self.gpio_request = self.gpiod.request_lines(
                    self.gpio_chip_path,
                    consumer="safety_control_node",
                    config={
                        self.gpio_line_number:
                        self.gpiod.LineSettings(
                            direction=self.Direction.INPUT
                        )
                    }
                )

                self.gpio_available = True

                self.get_logger().info(
                    'REAL HARDWARE MODE'
                )

            except Exception as e:

                self.get_logger().fatal(
                    f'GPIO INIT FAILED: {e}'
                )

                raise

        else:

            self.get_logger().info(
                'SIMULATION MODE'
            )

        # ======================================================
        # PARAMETERS
        # ======================================================

        self.normal_speed_limit = 100.0
        self.warning_speed_limit = 30.0
        self.estop_speed_limit = 0.0

        # ======================================================
        # STATES
        # ======================================================

        self.hardware_connected = False

        # GPIO ESTOP
        self.estop_gpio_active = False

        # Global scanner state:
        # NORMAL
        # WARNING
        # PROTECTIVE_STOP
        #
        self.safety_state = "NORMAL"

        self.current_speed_limit = -1.0

        self.last_connection_state = False
        self.last_safety_state = "INIT"

        # ======================================================
        # SUBSCRIBERS
        # ======================================================

        # ------------------------------------------------------
        # SICK SAFETY SCANNER OUTPUTS
        #
        # status[0] -> Protective Stop
        # status[1] -> Warning Field
        #
        # If ANY lidar reports:
        #
        # Protective Stop:
        #     -> GLOBAL ESTOP
        #
        # Warning Field:
        #     -> GLOBAL WARNING
        #
        # Protective Stop always has higher priority.
        #
        # ------------------------------------------------------

        self.front_scanner_sub = self.create_subscription(
            OutputPaths,
            '/lidars/front/output_paths',
            self.front_scanner_callback,
            10
        )

        self.rear_scanner_sub = self.create_subscription(
            OutputPaths,
            '/lidars/rear/output_paths',
            self.rear_scanner_callback,
            10
        )

        self.connected_sub = self.create_subscription(
            Bool,
            '/hardware/connected',
            self.connected_callback,
            10
        )

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # ======================================================
        # PUBLISHERS
        # ======================================================

        self.speed_limit_pub = self.create_publisher(
            SpeedLimit,
            '/speed_limit',
            10
        )

        self.estop_pub = self.create_publisher(
            Bool,
            '/safety/estop',
            10
        )

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/safety/cmd_vel',
            10
        )

        # ======================================================
        # SCANNER STATES
        # ======================================================

        self.front_protective_stop = False
        self.front_warning = False

        self.rear_protective_stop = False
        self.rear_warning = False

        # ======================================================
        # TIMER
        # ======================================================

        self.timer = self.create_timer(
            0.02,
            self.timer_callback
        )

        # ======================================================
        # INITIAL STATE
        # ======================================================

        self.publish_speed_limit(
            self.normal_speed_limit
        )

        self.get_logger().info(
            'Safety Control Node started'
        )

    # ==========================================================
    # FRONT SCANNER CALLBACK
    # ==========================================================

    def front_scanner_callback(self, msg: OutputPaths):

        self.front_protective_stop = False
        self.front_warning = False

        # status[0] = protective stop
        if len(msg.status) > 0:

            self.front_protective_stop = not msg.status[0]

        # status[1] = warning field
        if len(msg.status) > 1:

            self.front_warning = not msg.status[1]

        self.update_safety_state()

    # ==========================================================
    # REAR SCANNER CALLBACK
    # ==========================================================

    def rear_scanner_callback(self, msg: OutputPaths):

        self.rear_protective_stop = False
        self.rear_warning = False

        # status[0] = protective stop
        if len(msg.status) > 0:

            self.rear_protective_stop = not msg.status[0]

        # status[1] = warning field
        if len(msg.status) > 1:

            self.rear_warning = not msg.status[1]

        self.update_safety_state()

    # ==========================================================
    # UPDATE GLOBAL SAFETY STATE
    # ==========================================================

    def update_safety_state(self):

        protective_stop_active = (
            self.front_protective_stop or
            self.rear_protective_stop
        )

        warning_active = (
            self.front_warning or
            self.rear_warning
        )

        # Protective stop has highest priority
        if protective_stop_active:

            self.safety_state = "PROTECTIVE_STOP"

        elif warning_active:

            self.safety_state = "WARNING"

        else:

            self.safety_state = "NORMAL"

    # ==========================================================
    # HARDWARE CONNECTED CALLBACK
    # ==========================================================

    def connected_callback(self, msg: Bool):

        self.hardware_connected = msg.data

        if self.hardware_connected != self.last_connection_state:

            if self.hardware_connected:

                self.get_logger().info(
                    'MOTOR DRIVER CONNECTED'
                )

            else:

                self.get_logger().error(
                    'NO CONNECTION TO MOTOR DRIVER'
                )

            self.last_connection_state = (
                self.hardware_connected
            )

    # ==========================================================
    # CMD VEL CALLBACK
    # ==========================================================

    def cmd_vel_callback(self, msg: Twist):

        # BLOCK MOVEMENT ON ESTOP
        if self.is_estop_active():

            self.publish_zero_twist()
            return

        # BLOCK MOVEMENT ON LOST HARDWARE
        if not self.hardware_connected:

            self.publish_zero_twist()
            return

        # SAFE FORWARDING
        self.cmd_vel_pub.publish(msg)

    # ==========================================================
    # TIMER CALLBACK
    # ==========================================================

    def timer_callback(self):

        # ======================================================
        # GPIO ESTOP
        # ======================================================

        if not self.simulation_mode:

            try:

                gpio_state = self.gpio_request.get_value(
                    self.gpio_line_number
                )

                self.estop_gpio_active = bool(
                    gpio_state
                )

            except Exception as e:

                self.get_logger().error(
                    f'GPIO READ ERROR: {e}'
                )

                # Fail-safe behavior
                self.estop_gpio_active = True

        else:

            # No GPIO in simulation
            self.estop_gpio_active = False

        # ======================================================
        # ESTOP LOGIC
        # ======================================================

        estop_active = self.is_estop_active()

        estop_msg = Bool()
        estop_msg.data = estop_active

        self.estop_pub.publish(estop_msg)

        # ======================================================
        # SPEED LIMIT LOGIC
        # ======================================================

        speed_limit = self.normal_speed_limit

        # PROTECTIVE STOP
        if estop_active:

            speed_limit = self.estop_speed_limit

            self.publish_zero_twist()

        # WARNING FIELD
        elif self.safety_state == "WARNING":

            speed_limit = self.warning_speed_limit

        # NORMAL
        else:

            speed_limit = self.normal_speed_limit

        # ======================================================
        # SAFETY STATE LOGGING
        # ======================================================

        current_state = self.safety_state

        if self.estop_gpio_active:

            current_state = "GPIO_ESTOP"

        # Log only on state change
        if current_state != self.last_safety_state:

            if current_state == "PROTECTIVE_STOP":

                self.get_logger().error(
                    f'PROTECTIVE STOP ACTIVE -> '
                    f'Speed Limit {speed_limit}%'
                )

            elif current_state == "WARNING":

                self.get_logger().warn(
                    f'WARNING FIELD ACTIVE -> '
                    f'Speed Limit {speed_limit}%'
                )

            elif current_state == "GPIO_ESTOP":

                self.get_logger().error(
                    'GPIO ESTOP ACTIVE -> '
                    'Speed Limit 0%'
                )

            elif current_state == "NORMAL":

                self.get_logger().info(
                    'NORMAL OPERATION -> '
                    'Speed Limit 100%'
                )

            self.last_safety_state = current_state

        # ======================================================
        # PUBLISH SPEED LIMIT
        # ======================================================

        if speed_limit != self.current_speed_limit:

            self.publish_speed_limit(
                speed_limit
            )

    # ==========================================================
    # SPEED LIMIT PUBLISHER
    # ==========================================================

    def publish_speed_limit(self, value):

        self.current_speed_limit = value

        speed_msg = SpeedLimit()

        speed_msg.speed_limit = float(value)
        speed_msg.percentage = True

        self.speed_limit_pub.publish(speed_msg)

    # ==========================================================
    # ESTOP CHECK
    # ==========================================================

    def is_estop_active(self):

        # External GPIO ESTOP
        if self.estop_gpio_active:
            return True

        # Scanner protective stop
        if self.safety_state == "PROTECTIVE_STOP":
            return True

        return False

    # ==========================================================
    # ZERO TWIST
    # ==========================================================

    def publish_zero_twist(self):

        zero_msg = Twist()

        zero_msg.linear.x = 0.0
        zero_msg.linear.y = 0.0
        zero_msg.linear.z = 0.0

        zero_msg.angular.x = 0.0
        zero_msg.angular.y = 0.0
        zero_msg.angular.z = 0.0

        self.cmd_vel_pub.publish(
            zero_msg
        )

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def destroy_node(self):

        try:

            if self.gpio_available:

                self.gpio_request.release()

        except Exception:
            pass

        super().destroy_node()


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):

    rclpy.init(args=args)

    node = SafetyControlNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()