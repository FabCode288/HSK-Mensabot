#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TwistStamped
from std_msgs.msg import String
from std_msgs.msg import Bool

from enum import Enum


class FieldState(Enum):

    STOP = 0

    FORWARD = 1
    BACKWARD = 2

    ROTATE_LEFT = 3
    ROTATE_RIGHT = 4

    MANUAL_OVERRIDE = 5


class LidarFieldSelector(Node):

    def __init__(self):

        super().__init__('lidar_field_selector')

        # ============================================================
        # PARAMETERS
        # ============================================================

        self.declare_parameter('simulation', True)

        self.simulation = self.get_parameter(
            'simulation'
        ).get_parameter_value().bool_value

        # ============================================================
        # GPIO CONFIG
        # ============================================================

        # 4 Bit output lines
        self.gpio_pins = [22, 23, 24, 25, 26, 27]
        self.gpio_available = False

        self.gpio_requests = {}

        # Import GPIO ONLY on Raspberry Pi / real robot
        if not self.simulation:

            try:

                import gpiod # type: ignore #Not available in simulation environment
                from gpiod.line import Direction, Value # type: ignore

                self.gpiod = gpiod
                self.Direction = Direction
                self.Value = Value

                self.gpio_chip_path = "/dev/gpiochip4"

                for pin in self.gpio_pins:

                    gpio_request = self.gpiod.request_lines(
                        self.gpio_chip_path,
                        consumer="lidar_field_selector",
                        config={
                            pin:
                            self.gpiod.LineSettings(
                                direction=self.Direction.OUTPUT
                            )
                        }
                    )

                    self.gpio_requests[pin] = gpio_request

                    # Initialize High
                    gpio_request.set_value(
                        pin,
                        self.Value.ACTIVE
                    )

                self.gpio_available = True

                self.get_logger().info(
                    'GPIO initialized'
                )

            except Exception as e:

                self.get_logger().error(
                    f'GPIO initialization failed: {e}'
                )

        else:

            self.get_logger().info(
                'Simulation mode active -> GPIO disabled'
            )

        # ============================================================
        # CONFIG
        # ============================================================

        self.linear_threshold = 0.02
        self.angular_threshold = 0.05

        self.timeout_sec = 0.5

        self.manual_override_timeout_sec = 2.0

        # ============================================================
        # STATE
        # ============================================================

        self.current_state = FieldState.STOP

        self.last_cmd_time = self.get_clock().now()

        self.manual_override_active = False

        self.last_manual_override_msg_time = self.get_clock().now()

        # ============================================================
        # ROS INTERFACES
        # ============================================================

        self.cmd_vel_sub = self.create_subscription(
            TwistStamped,
            '/mensabot_base_controller/cmd_vel_out',
            self.cmd_vel_callback,
            10
        )

        self.manual_override_sub = self.create_subscription(
            Bool,
            '/safety/manual_override',
            self.manual_override_callback,
            10
        )

        self.field_state_pub = self.create_publisher(
            String,
            '/safety/field_state',
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.timer_callback
        )

        self.get_logger().info(
            'Lidar field selector started'
        )

        self.publish_state()

        self.set_gpio_state()

    # ============================================================
    # MANUAL OVERRIDE CALLBACK
    # ============================================================

    def manual_override_callback(self, msg: Bool):

        self.last_manual_override_msg_time = self.get_clock().now()

        previous_state = self.manual_override_active

        self.manual_override_active = msg.data

        if self.manual_override_active and not previous_state:

            self.get_logger().warn(
                'MANUAL OVERRIDE ACTIVE'
            )

        if self.manual_override_active:

            if self.current_state != FieldState.MANUAL_OVERRIDE:

                self.current_state = FieldState.MANUAL_OVERRIDE

                self.publish_state()

                self.set_gpio_state()

    # ============================================================
    # CMD VEL CALLBACK
    # ============================================================

    def cmd_vel_callback(self, msg: Twist):

        self.last_cmd_time = self.get_clock().now()

        if self.manual_override_active:
            return

        linear_x = msg.twist.linear.x
        angular_z = msg.twist.angular.z

        # Deadband
        if abs(linear_x) < self.linear_threshold:
            linear_x = 0.0

        if abs(angular_z) < self.angular_threshold:
            angular_z = 0.0

        new_state = self.determine_state(
            linear_x,
            angular_z
        )

        if new_state != self.current_state:

            self.current_state = new_state

            self.publish_state()

            self.set_gpio_state()

    # ============================================================
    # DETERMINE STATE
    # ============================================================

    def determine_state(
        self,
        linear_x: float,
        angular_z: float
    ) -> FieldState:

        # STOP
        if linear_x == 0.0 and angular_z == 0.0:
            return FieldState.STOP

        # PURE FORWARD / BACKWARD
        if linear_x > 0.0 and angular_z == 0.0:
            return FieldState.FORWARD

        if linear_x < 0.0 and angular_z == 0.0:
            return FieldState.BACKWARD

        # PURE ROTATION
        if linear_x == 0.0 and angular_z > 0.0:
            return FieldState.ROTATE_LEFT

        if linear_x == 0.0 and angular_z < 0.0:
            return FieldState.ROTATE_RIGHT

        # COMBINED MOVEMENT
        # Forward / Backward has priority

        if linear_x > 0.0:
            return FieldState.FORWARD

        if linear_x < 0.0:
            return FieldState.BACKWARD

        return FieldState.STOP

    # ============================================================
    # GPIO OUTPUT
    # ============================================================

    def set_gpio_state(self):

        self.get_logger().info(
            f'Field state: {self.current_state.name}'
        )

        if not self.gpio_available:
            return

        # All outputs LOW
        for pin in self.gpio_pins:

            self.gpio_requests[pin].set_value(
                pin,
                self.Value.ACTIVE
            )

        active_pin = None

        if self.current_state == FieldState.FORWARD:
            active_pin = 22

        elif self.current_state == FieldState.BACKWARD:
            active_pin = 23

        elif self.current_state == FieldState.ROTATE_LEFT:
            active_pin = 24

        elif self.current_state == FieldState.ROTATE_RIGHT:
            active_pin = 24

        elif self.current_state == FieldState.MANUAL_OVERRIDE:
            active_pin = 26

        elif self.current_state == FieldState.STOP:
            return

        if active_pin is not None:

            self.gpio_requests[27].set_value(
                    27,
                    self.Value.INACTIVE
                )

            self.gpio_requests[active_pin].set_value(
                active_pin,
                self.Value.INACTIVE
            )

    # ============================================================
    # STATE PUBLISHER
    # ============================================================

    def publish_state(self):

        msg = String()

        msg.data = self.current_state.name

        self.field_state_pub.publish(msg)

    # ============================================================
    # TIMEOUT HANDLING
    # ============================================================

    def timer_callback(self):

        now = self.get_clock().now()

        manual_override_delta = (
            now - self.last_manual_override_msg_time
        ).nanoseconds / 1e9

        if self.manual_override_active:

            if manual_override_delta > self.manual_override_timeout_sec:

                self.manual_override_active = False

                self.get_logger().warn(
                    'MANUAL OVERRIDE TIMEOUT -> returning to normal field selection'
                )

                self.current_state = FieldState.STOP

                self.publish_state()

                self.set_gpio_state()

        delta = (
            now - self.last_cmd_time
        ).nanoseconds / 1e9

        if delta > self.timeout_sec:

            if self.current_state != FieldState.STOP:

                if not self.manual_override_active:

                    self.current_state = FieldState.STOP

                    self.publish_state()

                    self.set_gpio_state()

                    self.get_logger().warn(
                        'cmd_vel timeout -> STOP field activated'
                    )

    # ============================================================
    # CLEANUP
    # ============================================================

    def destroy_node(self):

        if self.gpio_available:

            for pin in self.gpio_pins:

                self.gpio_requests[pin].set_value(
                    pin,
                    self.Value.ACTIVE
                )

                self.gpio_requests[pin].release()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = LidarFieldSelector()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()