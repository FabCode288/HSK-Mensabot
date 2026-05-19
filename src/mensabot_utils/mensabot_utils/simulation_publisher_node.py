#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from std_msgs.msg import Bool


class SafetySimInputs(Node):

    def __init__(self):

        super().__init__('safety_sim_inputs')

        # ======================================================
        # DESCRIPTION
        # ======================================================
        #
        # This node provides dummy safety signals for simulation.
        #
        # Purpose:
        # - Simulate hardware connection state
        # - Simulate safety scanner field output
        #
        # This allows the real Safety Control Node to run
        # unchanged in simulation and on the real robot.
        #
        # Published Topics:
        #
        # /hardware/connected
        #   TRUE  -> hardware available
        #
        # /sick_field_output
        #   FALSE -> no warning field active
        #
        # ======================================================

        # ======================================================
        # PUBLISHERS
        # ======================================================

        # Simulated hardware connection state
        self.connected_pub = self.create_publisher(
            Bool,
            '/hardware/connected',
            10
        )

        # Simulated safety scanner warning field
        self.warning_pub = self.create_publisher(
            Bool,
            '/sick_field_output',
            10
        )

        # ======================================================
        # TIMER
        # ======================================================
        #
        # Publish simulation states periodically.
        #
        # This ensures:
        # - Topics are continuously available
        # - Late subscribers still receive data
        # - Simulation behaves similar to real hardware
        #
        # ======================================================

        self.timer = self.create_timer(
            0.5,
            self.timer_callback
        )

        self.get_logger().info(
            'Safety Simulation Input Node started'
        )

    # ==========================================================
    # TIMER CALLBACK
    # ==========================================================

    def timer_callback(self):

        # ------------------------------------------------------
        # HARDWARE CONNECTED
        # ------------------------------------------------------
        #
        # Always publish TRUE in simulation.
        #
        # This simulates a connected motor driver /
        # hardware interface.
        #
        # ------------------------------------------------------

        connected_msg = Bool()

        connected_msg.data = True

        self.connected_pub.publish(
            connected_msg
        )

        # ------------------------------------------------------
        # SAFETY FIELD OUTPUT
        # ------------------------------------------------------
        #
        # Always publish FALSE.
        #
        # FALSE -> no warning field active
        #
        # This can later be extended to:
        # - simulated warning fields
        # - simulated ESTOP states
        # - automated safety testing
        #
        # ------------------------------------------------------

        warning_msg = Bool()

        warning_msg.data = False

        self.warning_pub.publish(
            warning_msg
        )


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):

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