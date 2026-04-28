from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
import os
import xacro
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_name = "rebob_sim_description"
    share_dir = get_package_share_directory(package_name)
    world_dir = os.path.join(share_dir, 'worlds')
    mesh_dir = os.path.join(world_dir, 'meshes')

    xacro_file = os.path.join(share_dir, 'urdf', 'minimal_robot.xacro')
    # robot_sdf = os.path.join(share_dir, 'sdf','rebob', 'model.sdf')
    # with open(robot_sdf, 'r') as infp:
    #     robot_desc = infp.read()
    robot_description_config = xacro.process_file(xacro_file)
    robot_urdf = robot_description_config.toxml()

    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='industrial-warehouse.sdf'
    )

    world_name_config = LaunchConfiguration('world_name')

    world_path = PathJoinSubstitution([
        share_dir, 
        'worlds',
        world_name_config
    ])

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot_urdf}
            # {'robot_description': robot_desc}
        ]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        # arguments=[robot_sdf]
    )

    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
                    launch_arguments={'gz_args': ['-r -v4 ',world_path],'on_exit_shutdown':'true'}.items()
                    # launch_arguments={'gz_args': ['-r -v4 ',os.path.join(world_dir, 'industrial-warehouse.sdf')],'on_exit_shutdown':'true'}.items()
                    # launch_arguments={'gz_args': ['-r -v4 ',os.path.join(world_dir, 'rocks_world.sdf')],'on_exit_shutdown':'true'}.items()
             )


    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', 'robot_description',
                                   '-name', 'rebob',
                                   '-z', '0.1'],
                        output='screen')
    # spawn_entity = IncludeLaunchDescription(
    #             PythonLaunchDescriptionSource([os.path.join(
    #                 get_package_share_directory('ros_gz_sim'), 'launch', 'gz_spawn_model.launch.py')]),
    #                 launch_arguments={'file':robot_sdf,'entity_name':'rebob','z':'0.2'}.items()
    #                 # launch_arguments={'gz_args': ['-r -v4 ','/home/maks/ros2_foptd/src/rebob_sim_description/worlds/urban_simple_01/simple_urban_01.sdf'],'on_exit_shutdown':'true'}.items()
    #          )
    
    bridge_params = os.path.join(share_dir,'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"]
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"]
    )

    twist_stamper = Node(
        package='twist_stamper',
        executable='twist_stamper',
        parameters=[{'use_sim_time': True}],
        remappings=[('/cmd_vel_in','/diff_cont/cmd_vel_unstamped'),
                    ('/cmd_vel_out','/diff_cont/cmd_vel')]
    )

    # extended kalman filter
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(share_dir,'config','ekf.yaml'), {'use_sim_time': True}])
    

    foxglove = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge'
    )

    lidar_crop = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('rebob_sim_description'),
                'launch',
                'lidar_crop.launch.py'
            ])
        ])
    )

    packages_paths = [os.path.join(p, 'share') for p in os.getenv('AMENT_PREFIX_PATH').split(':')]
    gz_sim_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            mesh_dir + ':',
            ':' + ':'.join(packages_paths)])

    ld =  LaunchDescription([
        world_name_arg,
        robot_state_publisher_node,
        # joint_state_publisher_node,
        gazebo,
        spawn_entity,
        ros_gz_bridge,
        diff_drive_spawner,
        joint_broad_spawner,
        twist_stamper,
        ekf,
        foxglove,
        lidar_crop
    ])

    ld.add_action(gz_sim_resource_path)

    return ld
