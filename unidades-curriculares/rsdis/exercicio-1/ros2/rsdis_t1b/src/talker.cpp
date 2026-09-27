#include <memory>

#include "geometry_msgs/msg/pose.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char* argv[]) {
    // Inicializa o ROS 2 com os argumentos recebidos pelo programa.
    rclcpp::init(argc, argv);

    // Cria um nó com o nome "talker".
    auto node = std::make_shared<rclcpp::Node>("talker");

    // O publicador envia mensagens Pose no tópico pose_topic com fila de tamanho 10.
    auto publisher = node->create_publisher<geometry_msgs::msg::Pose>("pose_topic", 10);

    // A frequência de 1 Hz corresponde a uma publicação por segundo.
    rclcpp::Rate rate(1.0);

    // O ciclo continua enquanto o ROS 2 estiver em funcionamento.
    while (rclcpp::ok()) {
        // Em cada ciclo é criada uma nova mensagem Pose.
        geometry_msgs::msg::Pose message;

        // Define a posição nos três eixos do referencial.
        message.position.x = 1.0;
        message.position.y = 2.0;
        message.position.z = 0.0;

        // Este quaternion representa uma orientação sem rotação.
        message.orientation.x = 0.0;
        message.orientation.y = 0.0;
        message.orientation.z = 0.0;
        message.orientation.w = 1.0;

        RCLCPP_INFO(node->get_logger(),
                    "Publishing pose: position(%.2f, %.2f, %.2f), "
                    "orientation(%.2f, %.2f, %.2f, %.2f)",
                    message.position.x, message.position.y, message.position.z,
                    message.orientation.x, message.orientation.y, message.orientation.z,
                    message.orientation.w);

        // Publica a pose e processa eventuais callbacks pendentes do nó.
        publisher->publish(message);
        rclcpp::spin_some(node);
        // Espera o tempo necessário para manter a frequência de 1 Hz.
        rate.sleep();
    }

    rclcpp::shutdown();
    return 0;
}
