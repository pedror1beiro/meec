#include "ros/ros.h"
#include "std_msgs/Float32.h"

// Executada sempre que chega uma nova mensagem.
void floatCallback(const std_msgs::Float32::ConstPtr& msg) {
    ROS_INFO("I heard: [%f]", msg->data);
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "listener");
    ros::NodeHandle nh;

    // Subscreve float_topic e guarda até 1000 mensagens na fila.
    ros::Subscriber sub = nh.subscribe("float_topic", 1000, floatCallback);

    // Mantém o nó ativo e processa as mensagens recebidas.
    ros::spin();
    return 0;
}
