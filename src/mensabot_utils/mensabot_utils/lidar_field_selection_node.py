#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import String

from enum import Enum


class FieldState(Enum):

    STOP = 0

    FORWARD = 1
    BACKWARD = 2

    ROTATE_LEFT = 3
    ROTATE_RIGHT = 4

    FORWARD_LEFT = 5
    FORWARD_RIGHT = 6

    BACKWARD_LEFT = 7
    BACKWARD_RIGHT = 8


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
        self.gpio_pins = [27, 22, 23, 24]

        self.gpio_available = False

        self.gpio_requests = {}

        # Import GPIO ONLY on Raspberry Pi / real robot
        if not self.simulation:

            try:

                import gpiod
                from gpiod.line import Direction, Value

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

                    # Initialize LOW
                    gpio_request.set_value(
                        pin,
                        self.Value.INACTIVE
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

        # ============================================================
        # STATE
        # ============================================================

        self.current_state = FieldState.STOP

        self.last_cmd_time = self.get_clock().now()

        # ============================================================
        # ROS INTERFACES
        # ============================================================

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/safety/cmd_vel',
            self.cmd_vel_callback,
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

    # ============================================================
    # CMD VEL CALLBACK
    # ============================================================

    def cmd_vel_callback(self, msg: Twist):

        self.last_cmd_time = self.get_clock().now()

        linear_x = msg.linear.x
        angular_z = msg.angular.z

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
        if linear_x > 0.0 and angular_z > 0.0:
            return FieldState.FORWARD_LEFT

        if linear_x > 0.0 and angular_z < 0.0:
            return FieldState.FORWARD_RIGHT

        if linear_x < 0.0 and angular_z > 0.0:
            return FieldState.BACKWARD_LEFT

        if linear_x < 0.0 and angular_z < 0.0:
            return FieldState.BACKWARD_RIGHT

        return FieldState.STOP

    # ============================================================
    # GPIO OUTPUT
    # ============================================================

    def set_gpio_state(self):

        # 4 Bit encoding
        bit_pattern = self.get_bit_pattern(
            self.current_state
        )

        self.get_logger().info(
            f'Field state: {self.current_state.name} -> {bit_pattern}'
        )

        if not self.gpio_available:
            return

        for i, pin in enumerate(self.gpio_pins):

            value = (
                self.Value.ACTIVE
                if bit_pattern[i]
                else self.Value.INACTIVE
            )

            self.gpio_requests[pin].set_value(
                pin,
                value
            )

    # ============================================================
    # BIT ENCODING
    # ============================================================

    def get_bit_pattern(
        self,
        state: FieldState
    ):

        mapping = {

            FieldState.STOP:            [0, 0, 0, 0],

            FieldState.FORWARD:         [0, 0, 0, 1],
            FieldState.BACKWARD:        [0, 0, 1, 0],

            FieldState.ROTATE_LEFT:     [0, 0, 1, 1],
            FieldState.ROTATE_RIGHT:    [0, 1, 0, 0],

            # prepared for future use
            FieldState.FORWARD_LEFT:    [0, 1, 0, 1],
            FieldState.FORWARD_RIGHT:   [0, 1, 1, 0],

            FieldState.BACKWARD_LEFT:   [0, 1, 1, 1],
            FieldState.BACKWARD_RIGHT:  [1, 0, 0, 0],
        }

        return mapping[state]

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

        delta = (
            now - self.last_cmd_time
        ).nanoseconds / 1e9

        if delta > self.timeout_sec:

            if self.current_state != FieldState.STOP:

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
                    self.Value.INACTIVE
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