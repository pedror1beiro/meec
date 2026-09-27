#include "ros/ros.h"
#include "std_msgs/Float32.h"

int main(int argc, char **argv) {
    // Inicializa o ROS e dá a este nó o nome "talker".
    ros::init(argc, argv, "talker");
    // O NodeHandle permite criar publicadores e comunicar com o sistema ROS.
    ros::NodeHandle nh;
    // Publica mensagens Float32 no tópico float_topic, usando uma fila de 1000.
    ros::Publisher floatPublisher = nh.advertise<std_msgs::Float32>("float_topic", 1000);
    // Define a frequência do ciclo como 50 Hz.
    ros::Rate loopRate(50);

    // O ciclo continua enquanto o ROS estiver em funcionamento.
    while (ros::ok()) {
        // Cria a mensagem e coloca o valor de exemplo no campo data.
        std_msgs::Float32 msg;
        msg.data = 3.14;
        // Mostra o valor no terminal e publica-o no tópico.
        ROS_INFO("Publishing: %f", msg.data);
        floatPublisher.publish(msg);
        // Processa callbacks que possam estar pendentes neste nó.
        ros::spinOnce();
        // Espera o tempo necessário para manter a frequência de 50 Hz.
        loopRate.sleep();
    }
    return 0;
}
