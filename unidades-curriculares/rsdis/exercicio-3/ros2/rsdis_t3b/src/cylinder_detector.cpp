#include <cmath>
#include <functional>
#include <limits>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

class CylinderDetector : public rclcpp::Node
{
public:
  CylinderDetector()
  : Node("cylinder_detector")
  {
    /*
     * Diferenca minima entre duas medidas consecutivas
     * para considerar que existe uma descontinuidade.
     */
    this->declare_parameter<double>("jump_threshold", 0.30);

    /*
     * Intervalo de largura aceite para um cilindro.
     * Sao valores suficientemente largos para evitar
     * uma afinacao excessiva ao mundo de simulacao.
     */
    this->declare_parameter<double>("min_width", 0.10);
    this->declare_parameter<double>("max_width", 0.40);

    scan_sub_ =
      this->create_subscription<sensor_msgs::msg::LaserScan>(
        "/scan",
        rclcpp::SensorDataQoS(),
        std::bind(
          &CylinderDetector::scanCallback,
          this,
          std::placeholders::_1));

    RCLCPP_INFO(
      this->get_logger(),
      "Detector de cilindros iniciado.");
  }

private:
  static constexpr double PI =
    3.14159265358979323846;

  void scanCallback(
    const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    const double threshold =
      this->get_parameter("jump_threshold").as_double();

    bool cilindro = false;

    std::size_t pi = 0;

    int detected = 0;

    for (std::size_t i = 1;
         i < msg->ranges.size();
         ++i)
    {
      double current = msg->ranges[i];
      double previous = msg->ranges[i - 1];

      /*
       * O LiDAR pode devolver inf/nan.
       * Para a deteção das descontinuidades,
       * consideramos esses valores como range_max.
       */
      if (!std::isfinite(current)) {
        current = msg->range_max;
      }

      if (!std::isfinite(previous)) {
        previous = msg->range_max;
      }

      /*
       * Metodo indicado pela professora:
       *
       * diff = ranges[i] - ranges[i - 1]
       */
      const double diff =
        current - previous;

      /*
       * Pi:
       * a distancia diminui bruscamente.
       */
      if (
        std::abs(diff) > threshold &&
        diff < 0.0 &&
        !cilindro)
      {
        pi = i;
        cilindro = true;
      }

      /*
       * Pf:
       * a distancia aumenta bruscamente
       * depois de encontrado Pi.
       */
      else if (
        std::abs(diff) > threshold &&
        diff > 0.0 &&
        cilindro)
      {
        const std::size_t pf = i - 1;

        cilindro = false;

        if (processCandidate(msg, pi, pf)) {
          detected++;
        }
      }
    }

    RCLCPP_INFO_THROTTLE(
      this->get_logger(),
      *this->get_clock(),
      2000,
      "Cilindros detetados: %d",
      detected);
  }


  bool processCandidate(
    const sensor_msgs::msg::LaserScan::SharedPtr msg,
    std::size_t pi,
    std::size_t pf)
  {
    if (pf <= pi) {
      return false;
    }

    /*
     * Procurar uma distancia representativa
     * do objeto entre Pi e Pf.
     */
    double distance_sum = 0.0;
    int valid_points = 0;

    for (std::size_t i = pi;
         i <= pf;
         ++i)
    {
      const double distance =
        msg->ranges[i];

      if (std::isfinite(distance))
      {
        distance_sum += distance;
        valid_points++;
      }
    }

    if (valid_points == 0) {
      return false;
    }

    const double distance =
      distance_sum /
      static_cast<double>(valid_points);

    /*
     * Angulo ocupado pelo objeto.
     */
    const double angular_width =
      static_cast<double>(pf - pi) *
      msg->angle_increment;

    /*
     * Aproximacao da largura do objeto
     * observada pelo LiDAR.
     *
     * largura = 2 * r * sin(theta / 2)
     */
    const double width =
      2.0 *
      distance *
      std::sin(angular_width / 2.0);

    const double min_width =
      this->get_parameter("min_width").as_double();

    const double max_width =
      this->get_parameter("max_width").as_double();

    /*
     * Rejeitar segmentos que tenham uma largura
     * claramente incompatível com um cilindro.
     */
    if (
      width < min_width ||
      width > max_width)
    {
      return false;
    }

    /*
     * Centro angular entre Pi e Pf.
     */
    const std::size_t center_idx =
      (pi + pf) / 2;

    const double center_angle =
      msg->angle_min +
      static_cast<double>(center_idx) *
      msg->angle_increment;

    RCLCPP_INFO(
      this->get_logger(),
      "CILINDRO | Pi=%zu | Pf=%zu | "
      "largura=%.2f m | distancia=%.2f m | "
      "angulo=%.1f graus",
      pi,
      pf,
      width,
      distance,
      center_angle * 180.0 / PI);

    return true;
  }


  rclcpp::Subscription<
    sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  rclcpp::spin(
    std::make_shared<CylinderDetector>());

  rclcpp::shutdown();

  return 0;
}
