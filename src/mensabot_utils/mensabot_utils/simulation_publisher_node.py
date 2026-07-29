#!/usr/bin/env python3

"""
Provides simulated safety inputs for the Mensabot platform.

This node publishes dummy hardware connection and LiDAR safety scanner
messages, allowing the Safety Control Node to operate unchanged in the
simulation environment.
"""

import rclpy

from rclpy.node import Node

from std_msgs.msg import Bool

# SICK Safety Scanner Message
from sick_safetyscanners2_interfaces.msg import OutputPaths


class SafetySimInputs(Node):
    """
    ROS 2 node providing simulated safety hardware signals.
    """

    def __init__(self):
        """
        Initialize publishers, timers and simulation states.
        """

        super().__init__('safety_sim_inputs')

        # ======================================================
        # DESCRIPTION
        # ======================================================
        #
        # This node provides dummy safety scanner signals
        # for simulation.
        #
        # Purpose:
        # - Simulate hardware connection state
        # - Simulate front scanner output paths
        # - Simulate rear scanner output paths
        #
        # This allows the real Safety Control Node
        # to run unchanged in simulation.
        #
        # Published Topics:
        #
        # /hardware/connected
        #
        # /lidars/front/output_paths
        #
        # /lidars/rear/output_paths
        #
        # ======================================================

        # ======================================================
        # PUBLISHERS
        # ======================================================

        # Simulated hardware connection
        self.connected_pub = self.create_publisher(
            Bool,
            '/hardware/connected',
            10
        )

        # Simulated front safety scanner
        self.front_scanner_pub = self.create_publisher(
            OutputPaths,
            '/lidars/front/output_paths',
            10
        )

        # Simulated rear safety scanner
        self.rear_scanner_pub = self.create_publisher(
            OutputPaths,
            '/lidars/rear/output_paths',
            10
        )

        # ======================================================
        # TIMER
        # ======================================================

        self.timer = self.create_timer(
            0.5,
            self.timer_callback
        )

        # ======================================================
        # SIMULATION STATES
        # ======================================================
        #
        # Change these values for testing.
        #
        # TRUE  -> field free / safe
        # FALSE -> field violated
        #
        # status[0] -> protective stop field
        # status[1] -> warning field
        #
        # ======================================================

        self.front_protective_stop_safe = True
        self.front_warning_safe = True

        self.rear_protective_stop_safe = True
        self.rear_warning_safe = True

        self.get_logger().info(
            'Safety Simulation Input Node started'
        )

    # ==========================================================
    # TIMER CALLBACK
    # ==========================================================

    def timer_callback(self):
        """
        Publish simulated hardware connection and LiDAR safety scanner messages.
        """

        # ------------------------------------------------------
        # HARDWARE CONNECTED
        # ------------------------------------------------------

        connected_msg = Bool()

        connected_msg.data = True

        self.connected_pub.publish(
            connected_msg
        )

        # ------------------------------------------------------
        # FRONT SCANNER
        # ------------------------------------------------------

        front_msg = OutputPaths()

        # status[0] -> protective stop
        # status[1] -> warning field

        front_msg.status = [
            self.front_protective_stop_safe,
            self.front_warning_safe
        ]

        # Optional additional fields
        front_msg.is_safe = [True, True]
        front_msg.is_valid = [True, True]

        front_msg.active_monitoring_case = 1

        self.front_scanner_pub.publish(
            front_msg
        )

        # ------------------------------------------------------
        # REAR SCANNER
        # ------------------------------------------------------

        rear_msg = OutputPaths()

        rear_msg.status = [
            self.rear_protective_stop_safe,
            self.rear_warning_safe
        ]

        rear_msg.is_safe = [True, True]
        rear_msg.is_valid = [True, True]

        rear_msg.active_monitoring_case = 1

        self.rear_scanner_pub.publish(
            rear_msg
        )


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):
    """
    Start the Safety Simulation Input node.
    """

    rclpy.init(args=args)

    node = SafetySimInputs()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()