#include <memory>

#include "geometry_msgs/msg/pose.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char* argv[]) {
    // Inicializa o ROS 2 antes de criar qualquer nó.
    rclcpp::init(argc, argv);

    // Cria o nó subscritor com o nome "listener".
    auto node = std::make_shared<rclcpp::Node>("listener");

    // Subscreve mensagens Pose no mesmo tópico usado pelo publicador.
    auto subscription = node->create_subscription<geometry_msgs::msg::Pose>(
        // A fila tem profundidade 10 e a lambda é executada quando chega uma mensagem.
        "pose_topic", 10, [node](const geometry_msgs::msg::Pose::SharedPtr message) {
            // A captura de node permite usar o logger do nó dentro do callback.
            // O RCLCPP_INFO mostra no terminal todos os campos recebidos.
            RCLCPP_INFO(node->get_logger(),
                        "I heard pose: position(%.2f, %.2f, %.2f), "
                        "orientation(%.2f, %.2f, %.2f, %.2f)",
                        // Primeiro são apresentados os três valores da posição.
                        message->position.x, message->position.y, message->position.z,
                        // Depois são apresentados os quatro valores da orientação.
                        message->orientation.x, message->orientation.y, message->orientation.z,
                        message->orientation.w);
        });

    // O spin mantém o nó ativo e trata os callbacks até ser usado Ctrl+C.
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
