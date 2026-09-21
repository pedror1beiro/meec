#include <ros/ros.h>
#include <geometry_msgs/Pose.h>

int main(int argc, char **argv) {
  ros::init(argc, argv, "talker");
  ros::NodeHandle nh;
  ros::Publisher posePublisher = nh.advertise<geometry_msgs::Pose>("pose_topic", 1);
  ros::Rate loopRate(1); // 1 Hz

  while (ros::ok()) {
    geometry_msgs::Pose message;
    message.position.x = 1.0;
    message.position.y = 2.0;
    message.position.z = 0.0;
    message.orientation.x = 0.0;
    message.orientation.y = 0.0;
    message.orientation.z = 0.0;
    message.orientation.w = 1.0;
    
    ROS_INFO_STREAM(message);
    posePublisher.publish(message);
    ros::spinOnce();
    loopRate.sleep();
  }
  return 0;
}