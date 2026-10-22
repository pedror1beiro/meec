#include <cmath>
#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

class Explorer : public rclcpp::Node
{
public:
  Explorer()
  : Node("explorer")
  {
    scan_sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan",
      rclcpp::SensorDataQoS(),
      std::bind(
        &Explorer::scanCallback,
        this,
        std::placeholders::_1));

    cmd_pub_ =
      this->create_publisher<geometry_msgs::msg::TwistStamped>(
        "/cmd_vel", 10);

    RCLCPP_INFO(
      this->get_logger(),
      "Explorer iniciado.");
  }

private:
  static constexpr double PI = 3.14159265358979323846;

  double normalizeAngle(double angle_deg)
  {
    while (angle_deg > 180.0) {
      angle_deg -= 360.0;
    }

    while (angle_deg < -180.0) {
      angle_deg += 360.0;
    }

    return angle_deg;
  }

  /*
   * Calcula a percentagem de ocupacao de um setor.
   *
   * Um raio e considerado ocupado quando encontra
   * um obstaculo a menos de obstacle_distance.
   */
  double getOccupancy(
    const sensor_msgs::msg::LaserScan::SharedPtr msg,
    double min_angle_deg,
    double max_angle_deg,
    double obstacle_distance)
  {
    int total = 0;
    int occupied = 0;

    for (std::size_t i = 0; i < msg->ranges.size(); ++i)
    {
      const double distance = msg->ranges[i];

      const double angle_rad =
        msg->angle_min +
        static_cast<double>(i) *
        msg->angle_increment;

      const double angle_deg =
        normalizeAngle(
          angle_rad * 180.0 / PI);

      if (
        angle_deg >= min_angle_deg &&
        angle_deg <= max_angle_deg)
      {
        total++;

        /*
         * inf significa que nao existe
         * obstaculo detetado nessa direcao,
         * portanto conta como livre.
         */
        if (
          std::isfinite(distance) &&
          distance < obstacle_distance)
        {
          occupied++;
        }
      }
    }

    if (total == 0) {
      return 100.0;
    }

    return
      100.0 *
      static_cast<double>(occupied) /
      static_cast<double>(total);
  }

  void scanCallback(
    const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    /*
     * Setores indicados pela logica da aula:
     *
     * esquerda : +30 a +90 graus
     * frente   : -30 a +30 graus
     * direita  : -90 a -30 graus
     */

    const double obstacle_distance = 0.60;

    const double left =
      getOccupancy(
        msg,
        30.0,
        90.0,
        obstacle_distance);

    const double front =
      getOccupancy(
        msg,
        -30.0,
        30.0,
        obstacle_distance);

    const double right =
      getOccupancy(
        msg,
        -90.0,
        -30.0,
        obstacle_distance);

    geometry_msgs::msg::TwistStamped cmd;

    cmd.header.stamp =
      this->get_clock()->now();

    /*
     * Escolher o setor com menor percentagem
     * de ocupacao.
     *
     * Em empate damos prioridade a frente.
     */

    if (
      front <= left &&
      front <= right)
    {
      // Frente e o setor mais livre
      cmd.twist.linear.x = 0.15;
      cmd.twist.angular.z = 0.0;
    }

    else if (left < right)
    {
      // Esquerda e o setor mais livre
      cmd.twist.linear.x = 0.0;
      cmd.twist.angular.z = 0.5;
    }

    else
    {
      // Direita e o setor mais livre
      cmd.twist.linear.x = 0.0;
      cmd.twist.angular.z = -0.5;
    }

    RCLCPP_INFO_THROTTLE(
      this->get_logger(),
      *this->get_clock(),
      1000,
      "Ocupacao -> L: %.1f%% | F: %.1f%% | R: %.1f%%",
      left,
      front,
      right);

    cmd_pub_->publish(cmd);
  }

  rclcpp::Subscription<
    sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;

  rclcpp::Publisher<
    geometry_msgs::msg::TwistStamped>::SharedPtr cmd_pub_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  rclcpp::spin(
    std::make_shared<Explorer>());

  rclcpp::shutdown();

  return 0;
}
