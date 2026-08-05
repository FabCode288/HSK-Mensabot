/** ****************************************************************************************
*  This node presents a fast and precise method to estimate the planar motion of a lidar
*  from consecutive range scans. It is very useful for the estimation of the robot odometry from
*  2D laser range measurements.
*  This module is developed for mobile robots with innacurate or inexistent built-in odometry.
*  It allows the estimation of a precise odometry with low computational cost.
*  For more information, please refer to:
*
*  Planar Odometry from a Radial Laser Scanner. A Range Flow-based Approach. ICRA'16.
*  Available at: http://mapir.isa.uma.es/mapirwebsite/index.php/mapir-downloads/papers/217
*
* Maintainer: Javier G. Monroy
* MAPIR group: http://mapir.isa.uma.es/
*
* Modifications: Jeremie Deray
******************************************************************************************** */

#include "rf2o_laser_odometry/CLaserOdometry2DNode.h"

using namespace rf2o;

bool CLaserOdometry2DNode::setLaserPoseFromTf()
{
  bool retrieved = false;

  // Set laser pose on the robot (through tF)
  // This allow estimation of the odometry with respect to the robot base reference system.
  geometry_msgs::msg::TransformStamped tf_laser;
  try
  {
    tf_laser = buffer_->lookupTransform(base_frame_id, last_scan.header.frame_id, tf2::TimePointZero);
    retrieved = true;
  }
  catch (tf2::TransformException &ex)
  {
    RCLCPP_ERROR(get_logger(), "%s",ex.what());
    retrieved = false;
  }

  //TF:transform -> Eigen::Isometry3d
  tf2::Transform transform;
  tf2::convert(tf_laser.transform, transform);
  const tf2::Matrix3x3 &basis = transform.getBasis();
  Eigen::Matrix3d R;

  for(int r = 0; r < 3; r++)
    for(int c = 0; c < 3; c++)
      R(r,c) = basis[r][c];

  Pose3d laser_tf(R);

  const tf2::Vector3 &t = transform.getOrigin();
  laser_tf.translation()(0) = t[0];
  laser_tf.translation()(1) = t[1];
  laser_tf.translation()(2) = t[2];

  rf2o_ref.setLaserPose(laser_tf);

  return retrieved;
}

bool CLaserOdometry2DNode::scan_available()
{
  return new_scan_available;
}

void CLaserOdometry2DNode::process()
{

  if( rf2o_ref.is_initialized() && scan_available() )
  {
    //Process odometry estimation
    rf2o_ref.odometryCalculation(last_scan);
    publish();
    new_scan_available = false; //avoids the possibility to run twice on the same laser scan
  }
  else
  {
    RCLCPP_WARN(get_logger(), "Waiting for laser_scans....") ;
  }
}

//-----------------------------------------------------------------------------------
//                                   CALLBACKS
//-----------------------------------------------------------------------------------

void CLaserOdometry2DNode::LaserCallBack(const sensor_msgs::msg::LaserScan::SharedPtr new_scan)
{
  if (GT_pose_initialized)
  {
    //Keep in memory the last received laser_scan
    last_scan = *new_scan;
    rf2o_ref.current_scan_time = last_scan.header.stamp;

    //Initialize module on first scan
    if (rf2o_ref.first_laser_scan == false)
    {
      //copy laser scan to internal variable
      for (unsigned int i = 0; i < rf2o_ref.width; i++)
        rf2o_ref.range_wf(i) = new_scan->ranges[i];
      new_scan_available = true;
    }
    else
    {
      setLaserPoseFromTf();
      rf2o_ref.init(last_scan, initial_robot_pose.pose.pose);
      rf2o_ref.first_laser_scan = false;
    }
  }
}

void CLaserOdometry2DNode::initPoseCallBack(const nav_msgs::msg::Odometry::SharedPtr new_initPose)
{
  //Initialize module on first GT pose. Else do Nothing!
  if (!GT_pose_initialized)
  {
    initial_robot_pose = *new_initPose;
    GT_pose_initialized = true;
  }
}

void CLaserOdometry2DNode::publish()
{
  //first, we'll publish the odometry over tf
  //---------------------------------------

  //next, we'll publish the odometry message over ROS
  //-------------------------------------------------
  
  RCLCPP_DEBUG(get_logger(), "[rf2o] Publishing Odom Topic");
  tf2::Quaternion tf_quaternion;
  tf_quaternion.setRPY(0.0, 0.0, rf2o::getYaw(rf2o_ref.robot_pose_.rotation()));
  geometry_msgs::msg::Quaternion quaternion = tf2::toMsg(tf_quaternion);
  nav_msgs::msg::Odometry odom;

  odom.header.stamp = rf2o_ref.last_odom_time;
  odom.header.frame_id = odom_frame_id;
  //set the position
  odom.pose.pose.position.x = rf2o_ref.robot_pose_.translation()(0);
  odom.pose.pose.position.y = rf2o_ref.robot_pose_.translation()(1);
  odom.pose.pose.position.z = 0.0;
  odom.pose.pose.orientation = quaternion;
  //set the velocity
  odom.child_frame_id = base_frame_id;
  odom.twist.twist.linear.x = rf2o_ref.lin_speed;    //linear speed
  odom.twist.twist.linear.y = 0.0;
  odom.twist.twist.angular.z = rf2o_ref.ang_speed;   //angular speed

  // ------------------------------------------------------------
  // Covariance
  // RF2O computes the covariance of the incremental motion
  // (vx, vy, wz). Publish it in the ROS Odometry message.
  // ------------------------------------------------------------

  const auto& cov = rf2o_ref.getIncrementCovariance();

  odom.pose.covariance.fill(0.0);
  odom.twist.covariance.fill(0.0);

  // Pose covariance (estimated)
  // x
  odom.pose.covariance[0] = 0.2;
  // y
  odom.pose.covariance[7] = 0.2;
  // yaw
  odom.pose.covariance[35] = 0.20;

  // Twist covariance
  // vx
  odom.twist.covariance[0] = cov(0,0);
  // vx <-> vy
  odom.twist.covariance[1] = cov(0,1);
  // vx <-> wz
  odom.twist.covariance[5] = cov(0,2);

  // vy <-> vx
  odom.twist.covariance[6] = cov(1,0);
  // vy
  odom.twist.covariance[7] = cov(1,1);
  // vy <-> wz
  odom.twist.covariance[11] = cov(1,2);

  // wz <-> vx
  odom.twist.covariance[30] = cov(2,0);
  // wz <-> vy
  odom.twist.covariance[31] = cov(2,1);
  // wz
  odom.twist.covariance[35] = cov(2,2);

  // Large uncertainty for unused DOFs
  odom.pose.covariance[14] = 99999.1;
  odom.pose.covariance[21] = 99999.1;
  odom.pose.covariance[28] = 99999.1;

  odom.twist.covariance[14] = 99999.1;
  odom.twist.covariance[21] = 99999.1;
  odom.twist.covariance[28] = 99999.1;
  //publish the message
  odom_pub->publish(odom);

  if (publish_tf)
  {
    RCLCPP_DEBUG(get_logger(), "[rf2o] Publishing TF: [base_link] to [odom]");
    geometry_msgs::msg::TransformStamped odom_trans;
    odom_trans.header.stamp = rf2o_ref.last_odom_time;
    odom_trans.header.frame_id = odom_frame_id;
    odom_trans.child_frame_id = base_frame_id;
    odom_trans.transform.translation.x = rf2o_ref.robot_pose_.translation()(0);
    odom_trans.transform.translation.y = rf2o_ref.robot_pose_.translation()(1);
    odom_trans.transform.translation.z = 0.0;
    odom_trans.transform.rotation = quaternion;
    //send the transform
    odom_broadcaster->sendTransform(odom_trans);
  }

}

} /* namespace rf2o */

//-----------------------------------------------------------------------------------
//                                   MAIN
//-----------------------------------------------------------------------------------
int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto myLaserOdomNode = std::make_shared<rf2o::CLaserOdometry2DNode>() ;
  rclcpp::Rate rate(myLaserOdomNode->freq);
  while (rclcpp::ok()){
      myLaserOdomNode->process();
      rclcpp::spin_some(myLaserOdomNode);
      rate.sleep();
  }
  return 0;

}
