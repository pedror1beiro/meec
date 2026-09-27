#include "geometry_msgs/Pose.h"
#include "ros/ros.h"

// Esta função é executada sempre que o subscritor recebe uma Pose.
void poseCallback(const geometry_msgs::Pose& msg) {
    // A referência constante permite ler a mensagem sem a copiar nem alterar.
    // Aqui são mostrados no terminal os três valores da posição recebida.
    ROS_INFO("I heard pose: pos(%.2f, %.2f, %.2f)", msg.position.x, msg.position.y, msg.position.z);
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
