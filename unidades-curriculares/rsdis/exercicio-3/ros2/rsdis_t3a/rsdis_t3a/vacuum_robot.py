import math
from rclpy.qos import qos_profile_sensor_data
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped


class VacuumRobot(Node):

    def __init__(self):
        super().__init__('vacuum_robot')

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        self.publisher = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )

        self.get_logger().info('Vacuum Robot iniciado.')

    def get_min_distance(self, msg, min_angle, max_angle):
        """
        Retorna a menor distância medida pelo LiDAR
        entre min_angle e max_angle, em graus.
        """

        min_distance = float('inf')

        for i, distance in enumerate(msg.ranges):

            if math.isinf(distance) or math.isnan(distance):
                continue

            angle = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle)

            if min_angle <= angle_deg <= max_angle:
                if distance < min_distance:
                    min_distance = distance

        return min_distance

    def scan_callback(self, msg):

        # Dividir o LiDAR em três zonas
        front = self.get_min_distance(msg, -20, 20)
        left = self.get_min_distance(msg, 20, 80)
        right = self.get_min_distance(msg, -80, -20)

        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()

        # Obstáculo muito próximo
        if front < 0.25:

            cmd.twist.linear.x = -0.05

            if left > right:
                cmd.twist.angular.z = 0.6
            else:
                cmd.twist.angular.z = -0.6

        # Obstáculo à frente
        elif front < 0.50:

            cmd.twist.linear.x = 0.0

            if left > right:
                cmd.twist.angular.z = 0.5
            else:
                cmd.twist.angular.z = -0.5

        # Caminho livre
        else:

            cmd.twist.linear.x = 0.15

            # Pequena correção para evitar aproximar-se das paredes
            if left < 0.35:
                cmd.twist.angular.z = -0.15

            elif right < 0.35:
                cmd.twist.angular.z = 0.15

            else:
                cmd.twist.angular.z = 0.0

        self.publisher.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = VacuumRobot()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
