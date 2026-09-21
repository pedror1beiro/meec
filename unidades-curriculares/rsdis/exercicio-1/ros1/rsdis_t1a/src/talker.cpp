#include "ros/ros.h"
#include "std_msgs/Float32.h"

int main(int argc, char **argv) {
  ros::init(argc, argv, "talker");
  ros::NodeHandle nh;
  ros::Publisher floatPublisher = nh.advertise<std_msgs::Float32>("float_topic", 1000);
  ros::Rate loopRate(50); // 50 Hz

  while (ros::ok()) {
    std_msgs::Float32 msg;
    msg.data = 3.14; // Valor de exemplo
    ROS_INFO("Publishing: %f", msg.data);
    floatPublisher.publish(msg);
    ros::spinOnce();
    loopRate.sleep();
  }
  return 0;
}