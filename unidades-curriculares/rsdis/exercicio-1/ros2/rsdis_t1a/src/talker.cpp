#include <chrono>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

using namespace std::chrono_literals;

class FloatPublisher : public rclcpp::Node
{
public:
  FloatPublisher()
  : Node("talker")
  {
    publisher_ =
      create_publisher<std_msgs::msg::Float32>("float_topic", 10);

    timer_ = create_wall_timer(
      20ms,
      [this]() {
        std_msgs::msg::Float32 message;
        message.data = 3.14F;

        RCLCPP_INFO(get_logger(), "Publishing: %.2f", message.data);
        publisher_->publish(message);
      });
  }

private:
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<FloatPublisher>());
  rclcpp::shutdown();
  return 0;
}
