#include "ros/ros.h"
#include "std_msgs/Float32.h"

// Esta função é chamada sempre que chega uma mensagem ao subscritor.
void floatCallback(const std_msgs::Float32::ConstPtr& msg) {
    // O ConstPtr permite consultar a mensagem sem alterar o seu conteúdo.
    // O valor recebido está guardado no campo data.
    ROS_INFO("I heard: [%f]", msg->data);
}

int main(int argc, char** argv) {
    // Inicializa o ROS e define o nome deste nó como "listener".
    ros::init(argc, argv, "listener");
    // O NodeHandle é usado para criar a subscrição.
    ros::NodeHandle nh;
    // Subscreve o mesmo tópico usado pelo publicador.
    // A fila suporta 1000 mensagens e floatCallback trata cada mensagem recebida.
    ros::Subscriber sub = nh.subscribe("float_topic", 1000, floatCallback);
    // Mantém o nó à espera de mensagens até ser interrompido com Ctrl+C.
    ros::spin();
    return 0;
}
