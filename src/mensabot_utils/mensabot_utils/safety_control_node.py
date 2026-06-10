#!/usr/bin/env python3

import time

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

                import gpiod # type: ignore #Not available in simulation environment
                from gpiod.line import Direction, Value # type: ignore

                self.gpiod = gpiod
                self.Direction = Direction
                self.Value = Value

                # --------------------------------------------------
                # GPIO INPUT
                # HIGH -> relays released / safe
                # LOW  -> relays open / ESTOP
                # --------------------------------------------------

                self.relay_status_input_line = 13

                # --------------------------------------------------
                # GPIO OUTPUT
                # Relay reset pulse output
                # --------------------------------------------------

                self.relay_reset_output_line = 17

                self.gpio_chip_path = "/dev/gpiochip4"

                self.gpio_request = self.gpiod.request_lines(
                    self.gpio_chip_path,
                    consumer="safety_control_node",
                    config={

                        # INPUT
                        self.relay_status_input_line:
                        self.gpiod.LineSettings(
                            direction=self.Direction.INPUT
                        ),

                        # OUTPUT
                        self.relay_reset_output_line:
                        self.gpiod.LineSettings(
                            direction=self.Direction.OUTPUT,
                            output_value=self.Value.INACTIVE
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
        # RESET CONFIG
        # ======================================================

        self.reset_interval = 1.0
        self.reset_pulse_duration = 0.5

        self.last_reset_attempt_time = 0.0
        self.reset_pulse_active = False
        self.reset_pulse_start_time = 0.0

        # ======================================================
        # STATES
        # ======================================================

        self.hardware_connected = False

        # HIGH -> relays not released
        self.estop_gpio_active = False

        # Global scanner state:
        # NORMAL
        # WARNING
        # PROTECTIVE_STOP
        #
        self.safety_state = "PROTECTIVE_STOP"

        self.current_speed_limit = -1.0

        self.last_connection_state = False
        self.last_safety_state = "INIT"

        # ======================================================
        # SUBSCRIBERS
        # ======================================================

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
    # 0 and 2 are protective stop fields
    # 1 and 3 are warning fields

    def front_scanner_callback(self, msg: OutputPaths):

        self.front_protective_stop = any(
            len(msg.status) > i and not msg.status[i]
            for i in [0]#x, 2]
        )

        self.front_warning = any(
            len(msg.status) > i and not msg.status[i]
            for i in [1]#, 3]
        )

        self.update_safety_state()

    # ==========================================================
    # REAR SCANNER CALLBACK
    # ==========================================================

    def rear_scanner_callback(self, msg: OutputPaths):

        self.rear_protective_stop = any(
            len(msg.status) > i and not msg.status[i]
            for i in [0]#, 2]
        )

        self.rear_warning = any(
            len(msg.status) > i and not msg.status[i]
            for i in [1]#, 3]
        )

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
        # GPIO RELAY STATUS INPUT
        # ======================================================

        if not self.simulation_mode:

            try:

                gpio_state = self.gpio_request.get_value(
                    self.relay_status_input_line
                )

                # HIGH -> relays open
                self.estop_gpio_active = not bool(
                    gpio_state
                )
                self.get_logger().debug(
                    f'GPIO State: {gpio_state} -> '
                    f'Estop Active: {self.estop_gpio_active}'
                )

            except Exception as e:

                self.get_logger().error(
                    f'GPIO READ ERROR: {e}'
                )

                # Fail-safe behavior
                self.estop_gpio_active = True

        else:

            self.estop_gpio_active = False

        # ======================================================
        # AUTOMATIC RELAY RESET
        # ======================================================

        current_time = time.time()

        # ------------------------------------------------------
        # START RESET PULSE
        # ------------------------------------------------------

        should_attempt_reset = (
            not self.simulation_mode and
            self.safety_state == "NORMAL" and
            self.estop_gpio_active and
            not self.reset_pulse_active and
            (current_time - self.last_reset_attempt_time)
            >= self.reset_interval
        )

        if should_attempt_reset:

            self.get_logger().info('ATTEMPTING SAFETY RELAY RESET')
            
            #self.get_logger().info(f'Safety relay Input: {self.estop_gpio_active}')

            try:

                # Set reset output HIGH
                self.gpio_request.set_value(
                    self.relay_reset_output_line,
                    self.Value.ACTIVE
                )

                self.reset_pulse_active = True

                self.reset_pulse_start_time = (
                    current_time
                )

                self.last_reset_attempt_time = (
                    current_time
                )

            except Exception as e:

                self.get_logger().error(
                    f'RELAY RESET FAILED: {e}'
                )

        # ------------------------------------------------------
        # END RESET PULSE
        # ------------------------------------------------------

        if self.reset_pulse_active:

            pulse_finished = (
                current_time -
                self.reset_pulse_start_time
            ) >= self.reset_pulse_duration

            if pulse_finished:

                try:
                    self.gpio_request.set_value(           # Set reset output LOW
                        self.relay_reset_output_line,
                        self.Value.INACTIVE
                    )

                    self.reset_pulse_active = False

                except Exception as e:

                    self.get_logger().error(
                        f'RESET PULSE END FAILED: {e}'
                    )

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

                self.get_logger().info(
                    f'PROTECTIVE STOP ACTIVE -> '
                    f'Speed Limit {speed_limit}%'
                )

            elif current_state == "WARNING":

                self.get_logger().info(
                    f'WARNING FIELD ACTIVE -> '
                    f'Speed Limit {speed_limit}%'
                )

            elif current_state == "GPIO_ESTOP":

                self.get_logger().error(
                    'SAFETY RELAYS OPEN -> '
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

        # Safety relays open
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