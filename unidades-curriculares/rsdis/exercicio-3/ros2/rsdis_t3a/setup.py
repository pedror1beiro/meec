from setuptools import find_packages, setup

package_name = 'rsdis_t3a'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='francisco-liquito',
    maintainer_email='todo@todo.com',
    description='Autonomous exploration with TurtleBot3',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vacuum_robot = rsdis_t3a.vacuum_robot:main',
        ],
    },
)
