#include <memory>

#include "geometry_msgs/msg/pose.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);

    auto node = std::make_shared<rclcpp::Node>("listener");

    // Subscreve pose_topic com profundidade QoS 10.
    auto subscription = node->create_subscription<geometry_msgs::msg::Pose>(
        "pose_topic", 10, [node](const geometry_msgs::msg::Pose::SharedPtr message) {
            // Apresenta todos os campos da posição e da orientação.
            RCLCPP_INFO(node->get_logger(),
                        "I heard pose: position(%.2f, %.2f, %.2f), "
                        "orientation(%.2f, %.2f, %.2f, %.2f)",
                        message->position.x, message->position.y, message->position.z,
                        message->orientation.x, message->orientation.y, message->orientation.z,
                        message->orientation.w);
        });

    // Mantém o nó ativo e processa as mensagens recebidas.
    rclcpp::spin(node);

    rclcpp::shutdown();
    return 0;
}
