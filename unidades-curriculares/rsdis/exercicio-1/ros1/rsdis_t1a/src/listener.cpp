#include "ros/ros.h"
#include "std_msgs/Float32.h"

void floatCallback(const std_msgs::Float32::ConstPtr& msg) { ROS_INFO("I heard: [%f]", msg->data); }

int main(int argc, char** argv) {
    ros::init(argc, argv, "listener");
    ros::NodeHandle nh;
    ros::Subscriber sub = nh.subscribe("float_topic", 1000, floatCallback);
    ros::spin();
    return 0;
}