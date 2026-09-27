#include "ros/ros.h"
#include "std_msgs/Float32.h"

int main(int argc, char **argv) {
    ros::init(argc, argv, "talker");
    ros::NodeHandle nh;

    // Publica mensagens Float32 no tópico float_topic.
    ros::Publisher floatPublisher = nh.advertise<std_msgs::Float32>("float_topic", 1000);

    // Mantém a publicação a 50 Hz.
    ros::Rate loopRate(50);

    while (ros::ok()) {
        std_msgs::Float32 msg;
        msg.data = 3.14;

        ROS_INFO("Publishing: %f", msg.data);
        floatPublisher.publish(msg);

        ros::spinOnce();
        loopRate.sleep();
    }
    return 0;
}
