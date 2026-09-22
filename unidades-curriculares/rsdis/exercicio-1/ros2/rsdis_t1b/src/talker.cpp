#include <memory>

#include "geometry_msgs/msg/pose.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>("talker");

  auto publisher =
    node->create_publisher<geometry_msgs::msg::Pose>("pose_topic", 10);

  rclcpp::Rate rate(1.0);

  while (rclcpp::ok()) {
    geometry_msgs::msg::Pose message;

    message.position.x = 1.0;
    message.position.y = 2.0;
    message.position.z = 0.0;

    message.orientation.x = 0.0;
    message.orientation.y = 0.0;
    message.orientation.z = 0.0;
    message.orientation.w = 1.0;

    RCLCPP_INFO(
      node->get_logger(),
      "Publishing pose: position(%.2f, %.2f, %.2f), "
      "orientation(%.2f, %.2f, %.2f, %.2f)",
      message.position.x,
      message.position.y,
      message.position.z,
      message.orientation.x,
      message.orientation.y,
      message.orientation.z,
      message.orientation.w);

    publisher->publish(message);
    rclcpp::spin_some(node);
    rate.sleep();
  }

  rclcpp::shutdown();
  return 0;
}
