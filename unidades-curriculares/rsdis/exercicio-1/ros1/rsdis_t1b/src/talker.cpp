#include <geometry_msgs/Pose.h>
#include <ros/ros.h>

int main(int argc, char **argv) {
    // Inicializa o ROS e dá ao nó o nome "talker".
    ros::init(argc, argv, "talker");
    // O NodeHandle permite criar o publicador.
    ros::NodeHandle nh;
    // Publica mensagens Pose no tópico pose_topic com uma fila de tamanho 1.
    ros::Publisher posePublisher = nh.advertise<geometry_msgs::Pose>("pose_topic", 1);
    // A frequência de 1 Hz corresponde a uma publicação por segundo.
    ros::Rate loopRate(1);

    // O ciclo termina quando o ROS for desligado ou for usado Ctrl+C.
    while (ros::ok()) {
        // A mensagem Pose guarda uma posição e uma orientação.
        geometry_msgs::Pose message;
        // Define a posição nos três eixos do referencial.
        message.position.x = 1.0;
        message.position.y = 2.0;
        message.position.z = 0.0;
        // Este quaternion representa uma orientação sem rotação.
        message.orientation.x = 0.0;
        message.orientation.y = 0.0;
        message.orientation.z = 0.0;
        message.orientation.w = 1.0;

        // Mostra a Pose no terminal e depois publica-a no tópico.
        ROS_INFO_STREAM(message);
        posePublisher.publish(message);
        // Processa callbacks pendentes e espera para manter a frequência de 1 Hz.
        ros::spinOnce();
        loopRate.sleep();
    }
    return 0;
}
