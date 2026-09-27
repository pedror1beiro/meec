#include <geometry_msgs/Pose.h>
#include <ros/ros.h>

int main(int argc, char **argv) {
    ros::init(argc, argv, "talker");
    ros::NodeHandle nh;

    // Publica mensagens Pose no tópico pose_topic.
    ros::Publisher posePublisher = nh.advertise<geometry_msgs::Pose>("pose_topic", 1);
    ros::Rate loopRate(1);  // 1 Hz

    // Publica uma nova Pose por segundo enquanto o ROS estiver ativo.
    while (ros::ok()) {
        geometry_msgs::Pose message;

        // Posição nos três eixos.
        message.position.x = 1.0;
        message.position.y = 2.0;
        message.position.z = 0.0;

        // Quaternion identidade: orientação sem rotação.
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
