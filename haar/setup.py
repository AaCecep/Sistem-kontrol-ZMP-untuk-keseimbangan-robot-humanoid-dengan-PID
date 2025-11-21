from setuptools import setup

package_name = 'haar'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        # index package
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        # package.xml
        ('share/' + package_name,
         ['package.xml']),
        # folder launch (supaya bisa: ros2 launch haar usb_cam_launch.py)
        ('share/' + package_name + '/launch',
         ['launch/usb_cam_launch.py',
          'launch/haar.py']),
        # kalau mau ikut meng-install cascade.xml juga (opsional tapi bagus)
        ('share/' + package_name,
         ['haar/cascade.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robotis',
    maintainer_email='robotis@example.com',
    description='Haar cascade robot detector for OP3',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # ros2 run haar haar
            # pastikan di file haar/haar.py ada fungsi main()
            'haar = haar.haar:main',
        ],
    },
)
