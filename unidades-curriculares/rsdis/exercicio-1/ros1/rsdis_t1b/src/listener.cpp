#include "geometry_msgs/Pose.h"
#include "ros/ros.h"

// Esta função é executada sempre que o subscritor recebe uma Pose.
void poseCallback(const geometry_msgs::Pose& msg) {
    // A referência constante permite ler a mensagem sem a copiar nem alterar.
    // Mostra no terminal todos os campos da posição e da orientação recebida.
    ROS_INFO("I heard pose: position(%.2f, %.2f, %.2f), "
             "orientation(%.2f, %.2f, %.2f, %.2f)",
             msg.position.x, msg.position.y, msg.position.z, msg.orientation.x,
             msg.orientation.y, msg.orientation.z, msg.orientation.w);
}

int main(int argc, char** argv) {
    // Inicializa o ROS e define o nome do nó como "listener".
    ros::init(argc, argv, "listener");
    // O NodeHandle é necessário para criar a subscrição.
    ros::NodeHandle nodeHandle;
    // Subscreve mensagens Pose publicadas no tópico pose_topic.
    // A fila guarda até 10 mensagens e poseCallback trata cada uma delas.
    ros::Subscriber subscriber = nodeHandle.subscribe("pose_topic", 10, poseCallback);
    // Mantém o nó ativo e executa os callbacks até ser usado Ctrl+C.
    ros::spin();
    return 0;
}
