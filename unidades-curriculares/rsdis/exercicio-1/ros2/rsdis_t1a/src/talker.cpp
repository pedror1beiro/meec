#include <chrono>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

// Permite escrever 20ms diretamente em vez de usar uma conversão manual.
using namespace std::chrono_literals;

// Este nó é responsável por publicar valores do tipo Float32.
class FloatPublisher : public rclcpp::Node {
   public:
    // O construtor também define o nome do nó como "talker".
    FloatPublisher() : Node("talker") {
        // Cria o publicador no tópico float_topic com profundidade de fila 10.
        publisher_ = create_publisher<std_msgs::msg::Float32>("float_topic", 10);

        // O temporizador chama esta função a cada 20 ms, ou seja, a 50 Hz.
        timer_ = create_wall_timer(20ms, [this]() {
            // A mensagem Float32 tem apenas o campo data, onde fica o valor enviado.
            std_msgs::msg::Float32 message;
            message.data = 3.14F;

            // Mostra o valor no terminal e depois publica-o no tópico.
            RCLCPP_INFO(get_logger(), "Publishing: %.2f", message.data);
            publisher_->publish(message);
        });
    }

   private:
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char* argv[]) {
    // Inicializa o ROS 2 e mantém o nó ativo até ser interrompido com Ctrl+C.
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<FloatPublisher>());
    rclcpp::shutdown();
    return 0;
}
