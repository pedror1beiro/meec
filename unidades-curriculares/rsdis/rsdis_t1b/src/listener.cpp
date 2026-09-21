#include "ros/ros.h"
#include "geometry_msgs/Pose.h"

void poseCallback(const geometry_msgs::Pose& msg) {
  ROS_INFO("I heard pose: pos(%.2f, %.2f, %.2f)",
           msg.position.x, msg.position.y, msg.position.z);
}

int main(int argc, char **argv) {
  ros::init(argc, argv, "listener");
  ros::NodeHandle nodeHandle;
  ros::Subscriber subscriber = nodeHandle.subscribe("pose_topic", 10, poseCallback);
  ros::spin();
  return 0;
}