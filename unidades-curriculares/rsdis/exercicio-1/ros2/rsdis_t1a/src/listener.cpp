#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

class FloatSubscriber : public rclcpp::Node {
   public:
    FloatSubscriber() : Node("listener") {
        // O tipo e o tópico devem coincidir com os usados pelo publicador.
        subscription_ = create_subscription<std_msgs::msg::Float32>(
            "float_topic", 10, [this](const std_msgs::msg::Float32::SharedPtr message) {
                RCLCPP_INFO(get_logger(), "I heard: %.2f", message->data);
            });
    }

   private:
    // Guardar a subscrição como membro mantém-na ativa durante a vida do nó.
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr subscription_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);

    // Aguarda mensagens e executa o callback do subscritor.
    rclcpp::spin(std::make_shared<FloatSubscriber>());

    rclcpp::shutdown();
    return 0;
}
