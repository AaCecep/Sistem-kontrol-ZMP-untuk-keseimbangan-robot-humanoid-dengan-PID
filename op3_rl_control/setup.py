from setuptools import find_packages, setup
from glob import glob
import os
from setuptools import setup

package_name = 'op3_rl_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yudhis',
    maintainer_email='yudhisthereal@gmail.com',
    description='RL live control interface for ROBOTIS OP3 in Webots',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cli_control_node = op3_rl_control.cli_control_node:main',
            'op3_cli = op3_rl_control.cli_interface:main',  # Add this line
        ],
    },
)