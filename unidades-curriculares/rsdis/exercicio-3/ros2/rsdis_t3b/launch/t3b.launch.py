import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    cartographer_launch = os.path.join(
        get_package_share_directory('turtlebot3_cartographer'),
        'launch',
        'cartographer.launch.py'
    )

    return LaunchDescription([

        Node(
            package='rsdis_t3b',
            executable='explorer',
            name='explorer',
            output='screen',
            parameters=[
                {'use_sim_time': True}
            ]
        ),

        Node(
            package='rsdis_t3b',
            executable='cylinder_detector',
            name='cylinder_detector',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'jump_threshold': 0.30},
                {'min_width': 0.10},
                {'max_width': 0.40}
            ]
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                cartographer_launch
            ),
            launch_arguments={
                'use_sim_time': 'true',
                'use_rviz': 'true'
            }.items()
        )
    ])
