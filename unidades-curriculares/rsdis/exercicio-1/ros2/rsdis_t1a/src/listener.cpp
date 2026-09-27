#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

// Este nó recebe os valores Float32 publicados pelo talker.
class FloatSubscriber : public rclcpp::Node {
   public:
    // O construtor define o nome deste nó como "listener".
    FloatSubscriber() : Node("listener") {
        // A subscrição tem de usar o mesmo tipo de mensagem e o mesmo tópico.
        subscription_ = create_subscription<std_msgs::msg::Float32>(
            // O valor 10 define a profundidade da fila de mensagens.
            "float_topic", 10, [this](const std_msgs::msg::Float32::SharedPtr message) {
                // Esta função de callback é chamada sempre que chega uma mensagem.
                // O valor recebido encontra-se no campo data da mensagem.
                RCLCPP_INFO(get_logger(), "I heard: %.2f", message->data);
            });
    }

   private:
    // Guardar a subscrição como membro evita que seja destruída no fim do construtor.
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr subscription_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    // O spin mantém o nó à espera de mensagens e executa os callbacks.
    rclcpp::spin(std::make_shared<FloatSubscriber>());
    rclcpp::shutdown();
    return 0;
}
