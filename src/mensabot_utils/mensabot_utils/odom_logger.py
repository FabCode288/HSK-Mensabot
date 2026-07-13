#!/usr/bin/env python3

import csv
import math
import os
import threading
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


# ============================================================
# Quaternion -> Yaw
# ============================================================

def quaternion_to_yaw(x, y, z, w):

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)

    return math.atan2(siny_cosp, cosy_cosp)


# ============================================================
# Pose Container
# ============================================================

class PoseData:

    def __init__(self):

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

    def copy(self):

        p = PoseData()

        p.x = self.x
        p.y = self.y
        p.yaw = self.yaw

        return p


# ============================================================
# Odom Logger
# ============================================================

class OdomLogger(Node):

    def __init__(self):

        super().__init__("odom_logger")

        # ----------------------------------------------------
        # Current poses
        # ----------------------------------------------------

        self.controller_pose = None
        self.rf2o_pose = None
        self.ekf_pose = None

        # ----------------------------------------------------
        # Start poses
        # ----------------------------------------------------

        self.controller_start = None
        self.rf2o_start = None
        self.ekf_start = None

        # ----------------------------------------------------
        # Subscribers
        # ----------------------------------------------------

        self.create_subscription(
            Odometry,
            "/mensabot_base_controller/odom",
            self.controller_callback,
            10
        )

        self.create_subscription(
            Odometry,
            "/odom_rf2o",
            self.rf2o_callback,
            10
        )

        self.create_subscription(
            Odometry,
            "/odom",
            self.ekf_callback,
            10
        )

        # ----------------------------------------------------
        # CSV Folder
        # ----------------------------------------------------

        self.output_folder = os.path.expanduser(
            "~/odom_validation"
        )

        os.makedirs(
            self.output_folder,
            exist_ok=True
        )

        filename = datetime.now().strftime(
            "odometry_validation_%Y_%m_%d.csv"
        )

        self.csv_path = os.path.join(
            self.output_folder,
            filename
        )

        if not os.path.exists(self.csv_path):

            with open(
                self.csv_path,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Trial",
                    "Source",
                    "Start_X",
                    "Start_Y",
                    "End_X",
                    "End_Y",
                    "Delta_X",
                    "Delta_Y",
                    "Distance",
                    "Start_Yaw",
                    "End_Yaw",
                    "Delta_Yaw"
                ])

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.measurement_running = False

        self.timer = self.create_timer(
            0.2,
            self.state_machine
        )

        self.get_logger().info(
            "Odom Logger started."
        )

    # ========================================================
    # Convert ROS Odometry -> PoseData
    # ========================================================

    def odom_to_pose(self, msg):

        pose = PoseData()

        pose.x = msg.pose.pose.position.x
        pose.y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation

        pose.yaw = quaternion_to_yaw(
            q.x,
            q.y,
            q.z,
            q.w
        )

        return pose

    # ========================================================
    # Callbacks
    # ========================================================

    def controller_callback(self, msg):

        self.controller_pose = self.odom_to_pose(msg)

    def rf2o_callback(self, msg):

        self.rf2o_pose = self.odom_to_pose(msg)

    def ekf_callback(self, msg):

        self.ekf_pose = self.odom_to_pose(msg)

    # ========================================================
    # Trial Number
    # ========================================================

    def get_trial_number(self):

        with open(self.csv_path) as file:

            lines = len(file.readlines())

        if lines <= 1:
            return 1

        return ((lines - 1) // 3) + 1

    # ========================================================
    # State Machine
    # ========================================================

    def state_machine(self):

        if self.measurement_running:
            return

        if (
            self.controller_pose is None or
            self.rf2o_pose is None or
            self.ekf_pose is None
        ):
            return

        self.measurement_running = True

        threading.Thread(
            target=self.measurement_thread,
            daemon=True
        ).start()

            # ========================================================
    # Measurement Thread
    # ========================================================

    def measurement_thread(self):

        print()
        print("=========================================")
        print("Mensabot Odometry Validation")
        print("=========================================")
        print()

        print("Place robot exactly on the start line.")
        print("The current pose will be stored in 5 seconds.")
        print()

        for i in range(5, 0, -1):

            print(f"Starting in {i} ...")
            time.sleep(1)

        # ----------------------------------------------------
        # Store start poses
        # ----------------------------------------------------

        self.controller_start = self.controller_pose.copy()
        self.rf2o_start = self.rf2o_pose.copy()
        self.ekf_start = self.ekf_pose.copy()

        print()
        print("Start pose stored.")
        print("Drive the robot manually to the finish line.")
        print()

        input("Press ENTER when the robot has stopped...")

        # ----------------------------------------------------
        # Store end poses
        # ----------------------------------------------------

        controller_end = self.controller_pose.copy()
        rf2o_end = self.rf2o_pose.copy()
        ekf_end = self.ekf_pose.copy()

        # Small pause to ensure last messages arrived
        time.sleep(0.2)

        self.evaluate(
            controller_end,
            rf2o_end,
            ekf_end
        )

        print()
        print("Measurement finished.")
        print()

        answer = input(
            "Start another measurement? (y/n): "
        )

        if answer.lower() == "y":

            self.measurement_running = False

        else:

            self.get_logger().info(
                "Logger stopped."
            )

            rclpy.shutdown()


    # ========================================================
    # Calculate travelled distance
    # ========================================================

    def calculate_values(
        self,
        start_pose,
        end_pose
    ):

        dx = end_pose.x - start_pose.x

        dy = end_pose.y - start_pose.y

        distance = math.sqrt(
            dx * dx +
            dy * dy
        )

        delta_yaw = end_pose.yaw - start_pose.yaw

        while delta_yaw > math.pi:
            delta_yaw -= 2.0 * math.pi

        while delta_yaw < -math.pi:
            delta_yaw += 2.0 * math.pi

        delta_yaw = math.degrees(delta_yaw)

        return (
            dx,
            dy,
            distance,
            delta_yaw
        )
        # ========================================================
    # Evaluate measurement
    # ========================================================

    def evaluate(
        self,
        controller_end,
        rf2o_end,
        ekf_end
    ):

        trial = self.get_trial_number()

        print()
        print("==============================================")
        print(f"RESULTS - TRIAL {trial}")
        print("==============================================")

        with open(
            self.csv_path,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            self.evaluate_source(
                writer,
                trial,
                "Controller",
                self.controller_start,
                controller_end
            )

            self.evaluate_source(
                writer,
                trial,
                "RF2O",
                self.rf2o_start,
                rf2o_end
            )

            self.evaluate_source(
                writer,
                trial,
                "EKF",
                self.ekf_start,
                ekf_end
            )

        print()
        print("CSV saved to:")
        print(self.csv_path)


    # ========================================================
    # Evaluate one odometry source
    # ========================================================

    def evaluate_source(
        self,
        writer,
        trial,
        source,
        start_pose,
        end_pose
    ):

        dx, dy, distance, delta_yaw = self.calculate_values(
            start_pose,
            end_pose
        )

        print()
        print("----------------------------------------------")
        print(source)
        print("----------------------------------------------")

        print(
            f"Start Pose : "
            f"({start_pose.x:.3f}, "
            f"{start_pose.y:.3f})"
        )

        print(
            f"End Pose   : "
            f"({end_pose.x:.3f}, "
            f"{end_pose.y:.3f})"
        )

        print(f"Δx         : {dx:.3f} m")
        print(f"Δy         : {dy:.3f} m")
        print(f"Distance   : {distance:.3f} m")

        print(
            f"Yaw Start  : "
            f"{math.degrees(start_pose.yaw):.2f} °"
        )

        print(
            f"Yaw End    : "
            f"{math.degrees(end_pose.yaw):.2f} °"
        )

        print(
            f"ΔYaw       : "
            f"{delta_yaw:.2f} °"
        )

        writer.writerow([
            trial,
            source,
            round(start_pose.x, 4),
            round(start_pose.y, 4),
            round(end_pose.x, 4),
            round(end_pose.y, 4),
            round(dx, 4),
            round(dy, 4),
            round(distance, 4),
            round(math.degrees(start_pose.yaw), 2),
            round(math.degrees(end_pose.yaw), 2),
            round(delta_yaw, 2)
        ])


# ============================================================
# Main
# ============================================================

def main(args=None):

    rclpy.init(args=args)

    node = OdomLogger()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":

    main()