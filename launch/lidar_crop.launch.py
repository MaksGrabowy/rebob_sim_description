from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='lidar_filter_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='pcl_ros',
                    plugin='pcl_ros::CropBox',
                    name='box_filter_node',
                    remappings=[
                        ('input', '/velodyne_scan'),
                        ('output', '/velodyne_points')
                    ],
                    parameters=[{
                        'input_frame': 'base_link',
                        'output_frame': 'laser_frame',
                        'min_x': -0.6, 'max_x': 0.6,
                        'min_y': -0.6, 'max_y': 0.6,
                        'min_z': -0.5, 'max_z': 1.0,
                        'negative': True,
                    }]
                ),
            ],
            output='screen',
        )
    ])