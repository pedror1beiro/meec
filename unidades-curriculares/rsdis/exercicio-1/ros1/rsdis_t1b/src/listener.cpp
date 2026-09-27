#include "geometry_msgs/Pose.h"
#include "ros/ros.h"

// Recebe e apresenta todos os campos da mensagem Pose.
void poseCallback(const geometry_msgs::Pose& msg) {
    ROS_INFO("I heard pose: position(%.2f, %.2f, %.2f), "
             "orientation(%.2f, %.2f, %.2f, %.2f)",
             msg.position.x, msg.position.y, msg.position.z, msg.orientation.x,
             msg.orientation.y, msg.orientation.z, msg.orientation.w);
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "listener");
    ros::NodeHandle nodeHandle;

    // Subscreve pose_topic com uma fila de 10 mensagens.
    ros::Subscriber subscriber = nodeHandle.subscribe("pose_topic", 10, poseCallback);

    // Mantém o nó ativo e processa as mensagens recebidas.
    ros::spin();
    return 0;
}
