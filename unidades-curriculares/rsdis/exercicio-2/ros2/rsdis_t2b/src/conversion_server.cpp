#include <cmath>
#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"

#include "rsdis_t2_interfaces/srv/r2_d.hpp"
#include "rsdis_t2_interfaces/srv/d2_r.hpp"
#include "rsdis_t2_interfaces/srv/g2_ecef.hpp"
#include "rsdis_t2_interfaces/srv/ecef2_g.hpp"

class ConversionServer : public rclcpp::Node
{
public:
  ConversionServer()
  : Node("conversion_server")
  {
    // Serviço para conversão de radianos para graus
    r2d_service_ =
      this->create_service<rsdis_t2_interfaces::srv::R2D>(
        "r2d",
        std::bind(
          &ConversionServer::r2d_callback,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    // Serviço para conversão de graus para radianos
    d2r_service_ =
      this->create_service<rsdis_t2_interfaces::srv::D2R>(
        "d2r",
        std::bind(
          &ConversionServer::d2r_callback,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    // Serviço para conversão de coordenadas geográficas para ECEF
    g2ecef_service_ =
      this->create_service<rsdis_t2_interfaces::srv::G2ECEF>(
        "g2ecef",
        std::bind(
          &ConversionServer::g2ecef_callback,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    // Serviço para conversão de ECEF para coordenadas geográficas
    ecef2g_service_ =
      this->create_service<rsdis_t2_interfaces::srv::ECEF2G>(
        "ecef2g",
        std::bind(
          &ConversionServer::ecef2g_callback,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    RCLCPP_INFO(
      this->get_logger(),
      "Servidor de conversoes pronto: r2d, d2r, g2ecef, ecef2g");
  }

private:
  // Parâmetros do sistema WGS84.
  // Fórmulas de conversão LLA <-> ECEF baseadas na ESA Navipedia:
  // https://gssc.esa.int/navipedia/index.php/Ellipsoidal_and_Cartesian_Coordinates_Conversion
  static constexpr double PI = 3.14159265358979323846;
  static constexpr double A = 6378137.0;
  static constexpr double F = 1.0 / 298.257223563;
  static constexpr double E2 = 2.0 * F - F * F;

  static double degrees_to_radians(double degrees)
  {
    return degrees * PI / 180.0;
  }

  static double radians_to_degrees(double radians)
  {
    return radians * 180.0 / PI;
  }

  // Conversão de radianos para graus
  void r2d_callback(
    const std::shared_ptr<rsdis_t2_interfaces::srv::R2D::Request> request,
    std::shared_ptr<rsdis_t2_interfaces::srv::R2D::Response> response)
  {
    response->degrees = radians_to_degrees(request->radians);

    RCLCPP_INFO(
      this->get_logger(),
      "r2d: %.10f rad -> %.10f deg",
      request->radians,
      response->degrees);
  }

  // Conversão de graus para radianos
  void d2r_callback(
    const std::shared_ptr<rsdis_t2_interfaces::srv::D2R::Request> request,
    std::shared_ptr<rsdis_t2_interfaces::srv::D2R::Response> response)
  {
    response->radians = degrees_to_radians(request->degrees);

    RCLCPP_INFO(
      this->get_logger(),
      "d2r: %.10f deg -> %.10f rad",
      request->degrees,
      response->radians);
  }

  // Conversão LLA WGS84 -> ECEF.
  // Implementação baseada nas fórmulas da ESA Navipedia.
  void g2ecef_callback(
    const std::shared_ptr<rsdis_t2_interfaces::srv::G2ECEF::Request> request,
    std::shared_ptr<rsdis_t2_interfaces::srv::G2ECEF::Response> response)
  {
    const double latitude =
      degrees_to_radians(request->latitude);

    const double longitude =
      degrees_to_radians(request->longitude);

    const double altitude = request->altitude;

    const double sin_lat = std::sin(latitude);
    const double cos_lat = std::cos(latitude);

    // Raio de curvatura da primeira vertical
    const double N =
      A / std::sqrt(1.0 - E2 * sin_lat * sin_lat);

    response->x =
      (N + altitude) *
      cos_lat *
      std::cos(longitude);

    response->y =
      (N + altitude) *
      cos_lat *
      std::sin(longitude);

    response->z =
      ((1.0 - E2) * N + altitude) *
      sin_lat;

    RCLCPP_INFO(
      this->get_logger(),
      "g2ecef: lat=%.8f lon=%.8f alt=%.3f -> x=%.3f y=%.3f z=%.3f",
      request->latitude,
      request->longitude,
      request->altitude,
      response->x,
      response->y,
      response->z);
  }

  // Conversão ECEF -> LLA WGS84.
  // Método iterativo baseado na ESA Navipedia.
  void ecef2g_callback(
    const std::shared_ptr<rsdis_t2_interfaces::srv::ECEF2G::Request> request,
    std::shared_ptr<rsdis_t2_interfaces::srv::ECEF2G::Response> response)
  {
    const double x = request->x;
    const double y = request->y;
    const double z = request->z;

    const double p = std::sqrt(x * x + y * y);

    // Cálculo direto da longitude
    const double longitude = std::atan2(y, x);

    // Caso especial: ponto situado no eixo de rotação da Terra
    if (p < 1e-12) {
      const double B = A * (1.0 - F);

      response->latitude =
        (z >= 0.0) ? 90.0 : -90.0;

      response->longitude = 0.0;
      response->altitude = std::abs(z) - B;

      return;
    }

    // Estimativa inicial da latitude
    double latitude =
      std::atan2(z, (1.0 - E2) * p);

    double altitude = 0.0;

    constexpr double tolerance = 1e-12;
    constexpr int max_iterations = 100;

    // Processo iterativo para determinação da latitude e altitude
    for (int i = 0; i < max_iterations; ++i) {
      const double sin_lat = std::sin(latitude);

      const double N =
        A / std::sqrt(1.0 - E2 * sin_lat * sin_lat);

      altitude =
        p / std::cos(latitude) - N;

      const double new_latitude =
        std::atan2(
          z,
          p * (1.0 - E2 * N / (N + altitude)));

      // Termina quando a variação da latitude é suficientemente pequena
      if (std::abs(new_latitude - latitude) < tolerance) {
        latitude = new_latitude;
        break;
      }

      latitude = new_latitude;
    }

    // Recalcula a altitude com o valor final da latitude
    const double sin_lat = std::sin(latitude);

    const double N =
      A / std::sqrt(1.0 - E2 * sin_lat * sin_lat);

    altitude =
      p / std::cos(latitude) - N;

    response->latitude =
      radians_to_degrees(latitude);

    response->longitude =
      radians_to_degrees(longitude);

    response->altitude =
      altitude;

    RCLCPP_INFO(
      this->get_logger(),
      "ecef2g: x=%.3f y=%.3f z=%.3f -> lat=%.8f lon=%.8f alt=%.3f",
      x,
      y,
      z,
      response->latitude,
      response->longitude,
      response->altitude);
  }

  rclcpp::Service<rsdis_t2_interfaces::srv::R2D>::SharedPtr
    r2d_service_;

  rclcpp::Service<rsdis_t2_interfaces::srv::D2R>::SharedPtr
    d2r_service_;

  rclcpp::Service<rsdis_t2_interfaces::srv::G2ECEF>::SharedPtr
    g2ecef_service_;

  rclcpp::Service<rsdis_t2_interfaces::srv::ECEF2G>::SharedPtr
    ecef2g_service_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  rclcpp::spin(
    std::make_shared<ConversionServer>());

  rclcpp::shutdown();

  return 0;
}
