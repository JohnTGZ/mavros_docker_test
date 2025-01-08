#!/usr/bin/env python

"""
Complete set of nodes required to simulate an agent (without dynamics)
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchContext
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction

from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():
    ''' Get launch argument values '''
    drone_id = LaunchConfiguration('drone_id')
    init_x = LaunchConfiguration('init_x')
    init_y = LaunchConfiguration('init_y')

    drone_id_launch_arg = DeclareLaunchArgument(
      'drone_id',
      default_value='0'
    )

    init_x_launch_arg = DeclareLaunchArgument(
      'init_x',
      default_value='0.0'
    )
    init_y_launch_arg = DeclareLaunchArgument(
      'init_y',
      default_value='0.0'
    )

    '''Frames'''
    map_frame = 'map'
    # map_frame = ['d', drone_id, '_origin']
    local_map_frame = ['d', drone_id, '_lcl_map']
    base_link_frame = 'base_link'
    # base_link_frame = ['d', drone_id, '_base_link']
    camera_frame = ['d', drone_id, '_camera_link']

    ''' Get directories '''
    px4_dir = os.path.join(
      os.path.expanduser("~"), 'PX4-Autopilot'
    )

    px4_build_dir = os.path.join(
      px4_dir, "build/px4_sitl_default"
    )

    ''' Get parameter files '''

    px4_pluginlists_cfg = os.path.join(
      get_package_share_directory('mavros_bridge'), 'config',
      'px4_pluginlists.yaml'
    )

    px4_config_cfg = os.path.join(
      get_package_share_directory('mavros_bridge'), 'config',
      'px4_config.yaml'
    )


    """Nodes"""
    # Publish TF for map to fixed drone origin
    # This is necessary because PX4 SITL is not able to change it's initial starting position
    drone_origin_tf = Node(package = "tf2_ros", 
                       executable = "static_transform_publisher",
                       output="log",
                      arguments = [init_x, init_y, "0", "0", "0", "0", 
                              "world", map_frame])

    # drone base_link to sensor fixed TF
    camera_link_tf = Node(package = "tf2_ros", 
                       executable = "static_transform_publisher",
                       output="log",
                      arguments = ["0", "0", "0", "0", "0", "0", 
                              base_link_frame, camera_frame])

    '''Mavlink/Mavros'''
    fcu_addr =  PythonExpression(['14540 +', drone_id])
    # fcu_port =  PythonExpression(['14580 +', drone_id])
    fcu_port =  PythonExpression(['14557 +', drone_id]) # Used for SITL
    fcu_url = ["udp://:", fcu_addr, "@localhost:", fcu_port] # udp://:14540@localhost:14557
    tgt_system = PythonExpression(['1 +', drone_id])

    mavros_node = Node(
      package='mavros',
      executable='mavros_node',
      output='screen',
      shell=False,
      namespace='mavros',
      parameters=[
        {'fcu_url': fcu_url},
        {'gcs_url': ''},
        {'tgt_system': tgt_system},
        {'tgt_component': 1},
        {'fcu_protocol': 'v2.0'},
        px4_pluginlists_cfg,
        px4_config_cfg,
        {'local_position.frame_id': map_frame},
        {'local_position.tf.send': 'true'},
        {'local_position.tf.frame_id': map_frame},
        {'local_position.tf.child_frame_id': base_link_frame},
      ],
      remappings=[
        ('local_position/odom', ['/d', drone_id, '/odom']),
      ],

    )

    return LaunchDescription([
        # Launch arguments
        drone_id_launch_arg,
        init_x_launch_arg,
        init_y_launch_arg,
        # Static transforms
        drone_origin_tf,
        camera_link_tf,
        # Mavlink to ROS bridge
        mavros_node,
        # Drone simulation instance
    ])
