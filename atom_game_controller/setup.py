from setuptools import setup

package_name = 'atom_game_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/gamecontroller.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your@email.com',
    description='ATOM Game Controller package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'game_controller = atom_game_controller.game_controller:main',
        ],
    },
)
