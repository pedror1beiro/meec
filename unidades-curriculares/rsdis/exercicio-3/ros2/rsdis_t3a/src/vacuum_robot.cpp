#include <cmath>
#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

class VacuumRobot : public rclcpp::Node
{
public:
  VacuumRobot()
  : Node("vacuum_robot")
  {
    scan_sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan",
      rclcpp::SensorDataQoS(),
      std::bind(
        &VacuumRobot::scanCallback,
        this,
        std::placeholders::_1));

    cmd_pub_ =
      this->create_publisher<geometry_msgs::msg::TwistStamped>(
        "/cmd_vel",
        10);

    RCLCPP_INFO(
      this->get_logger(),
      "Vacuum Robot iniciado.");
  }

private:
  static constexpr double PI =
    3.14159265358979323846;

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
   * Calcula a percentagem de ocupacao
   * de um setor do LiDAR.
   */
  double getOccupancy(
    const sensor_msgs::msg::LaserScan::SharedPtr msg,
    double min_angle_deg,
    double max_angle_deg,
    double obstacle_distance)
  {
    int total = 0;
    int occupied = 0;

    for (std::size_t i = 0;
         i < msg->ranges.size();
         ++i)
    {
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

        const double distance =
          msg->ranges[i];

        /*
         * Um raio conta como ocupado quando
         * encontra um obstaculo dentro da
         * distancia definida.
         *
         * inf/nan representam ausencia de
         * obstaculo proximo e contam como livre.
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
     * Divisao do campo de visao:
     *
     * direita  : -90 a -30 graus
     * frente   : -30 a +30 graus
     * esquerda : +30 a +90 graus
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
     * Escolher o setor menos ocupado.
     *
     * Em caso de empate, damos prioridade
     * a continuar em frente.
     */
    if (
      front <= left &&
      front <= right)
    {
      cmd.twist.linear.x = 0.15;
      cmd.twist.angular.z = 0.0;
    }
    else if (left < right)
    {
      cmd.twist.linear.x = 0.0;
      cmd.twist.angular.z = 0.5;
    }
    else
    {
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
    std::make_shared<VacuumRobot>());

  rclcpp::shutdown();

  return 0;
}
