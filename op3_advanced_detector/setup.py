from setuptools import find_packages, setup

package_name = 'op3_advanced_detector'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/ball_detector_from_usb_cam.launch.py',
            'launch/advanced_detector.launch.py',
            # Tambahkan file launch lain kalau ada
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robotis',
    maintainer_email='robotis@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'op3_advanced_detector = op3_advanced_detector.op3_advanced_detector:main'
        ],
    },
)
