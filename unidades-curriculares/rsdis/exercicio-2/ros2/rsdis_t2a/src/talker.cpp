#include <chrono>
#include <memory>
#include <random>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/nav_sat_status.hpp"
#include "rsdis_t2_interfaces/msg/sensor_data.hpp"

using namespace std::chrono_literals;

class SensorPublisher : public rclcpp::Node
{
public:
  SensorPublisher()
  : Node("sensor_publisher"),
    generator_(std::random_device{}()),
    temp_dist_(10.0, 35.0),
    humidity_dist_(0.20, 0.90),
    radiation_dist_(0.0, 10.0),
    latitude_dist_(51.35, 51.45),
    longitude_dist_(30.00, 30.20),
    altitude_dist_(100.0, 150.0)
  {
    publisher_ =
      this->create_publisher<rsdis_t2_interfaces::msg::SensorData>(
        "sensor_data", 10);

    timer_ = this->create_wall_timer(
      1s,
      std::bind(&SensorPublisher::publish_data, this));
  }

private:
  void publish_data()
  {
    rsdis_t2_interfaces::msg::SensorData message;

    // Um único timestamp para todas as leituras desta aquisição
    auto timestamp = this->get_clock()->now();

    // Header da mensagem global
    message.header.stamp = timestamp;
    message.header.frame_id = "ugv";

    // GPS
    message.gps.header.stamp = timestamp;
    message.gps.header.frame_id = "gps_sensor";

    message.gps.status.status =
      sensor_msgs::msg::NavSatStatus::STATUS_FIX;

    message.gps.status.service =
      sensor_msgs::msg::NavSatStatus::SERVICE_GPS;

    message.gps.latitude = latitude_dist_(generator_);
    message.gps.longitude = longitude_dist_(generator_);
    message.gps.altitude = altitude_dist_(generator_);

    // Temperatura
    message.temperature.header.stamp = timestamp;
    message.temperature.header.frame_id = "temperature_sensor";
    message.temperature.temperature = temp_dist_(generator_);
    message.temperature.variance = 0.0;

    // Humidade
    message.humidity.header.stamp = timestamp;
    message.humidity.header.frame_id = "humidity_sensor";
    message.humidity.relative_humidity = humidity_dist_(generator_);
    message.humidity.variance = 0.0;

    // Radiação - mensagem criada por nós
    message.radiation.header.stamp = timestamp;
    message.radiation.header.frame_id = "radiation_sensor";
    message.radiation.radiation = radiation_dist_(generator_);

    publisher_->publish(message);

    RCLCPP_INFO(
      this->get_logger(),
      "Publicado: Temp=%.2f C | Humidade=%.2f | Radiacao=%.2f",
      message.temperature.temperature,
      message.humidity.relative_humidity,
      message.radiation.radiation);
  }

  rclcpp::Publisher<
    rsdis_t2_interfaces::msg::SensorData>::SharedPtr publisher_;

  rclcpp::TimerBase::SharedPtr timer_;

  std::mt19937 generator_;

  std::uniform_real_distribution<double> temp_dist_;
  std::uniform_real_distribution<double> humidity_dist_;
  std::uniform_real_distribution<double> radiation_dist_;
  std::uniform_real_distribution<double> latitude_dist_;
  std::uniform_real_distribution<double> longitude_dist_;
  std::uniform_real_distribution<double> altitude_dist_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  rclcpp::spin(std::make_shared<SensorPublisher>());

  rclcpp::shutdown();

  return 0;
}
