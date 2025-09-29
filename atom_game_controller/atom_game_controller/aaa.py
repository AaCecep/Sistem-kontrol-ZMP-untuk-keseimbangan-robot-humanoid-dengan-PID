import socket
import struct
import threading
from typing import Optional, Callable

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from robocup_gamecontroller_msgs.msg import (
    RobotInfo, TeamInfo, GameControlData, GameControlReturnData
)
from .constants import *


class GameControllerNode(Node):
    """ROS2 Node for RoboCup Game Controller communication"""
    
    def __init__(self):
        super().__init__('robocup_game_controller')
        
        # Parameters
        self.declare_parameter('team_number', 1)
        self.declare_parameter('player_number', 1)
        self.declare_parameter('gamecontroller_ip', '255.255.255.255')
        self.declare_parameter('listen_port', GAMECONTROLLER_PORT)
        self.declare_parameter('send_alive_interval', 2.0)
        
        self.team_number = self.get_parameter('team_number').value
        self.player_number = self.get_parameter('player_number').value
        self.gc_ip = self.get_parameter('gamecontroller_ip').value
        self.listen_port = self.get_parameter('listen_port').value
        self.alive_interval = self.get_parameter('send_alive_interval').value
        
        # QoS profile for reliable communication
        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        
        # Publishers
        self.game_state_pub = self.create_publisher(
            GameControlData, 'robocup/game_state', qos
        )
        
        # Subscribers
        self.return_data_sub = self.create_subscription(
            GameControlReturnData,
            'robocup/return_data',
            self.return_data_callback,
            10
        )
        
        # UDP socket for receiving game controller data
        self.receive_socket = None
        self.send_socket = None
        self.receiver_thread = None
        self.running = False
        
        # Timer for sending alive messages
        self.alive_timer = self.create_timer(
            self.alive_interval, 
            self.send_alive_message
        )
        
        self.get_logger().info(f'GameController Node started')
        self.get_logger().info(f'Team: {self.team_number}, Player: {self.player_number}')
        
        # Start UDP communication
        self.start_udp_communication()
    
    def start_udp_communication(self):
        """Initialize UDP sockets and start receiving thread"""
        try:
            # Socket for receiving game controller data
            self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.receive_socket.bind(('', self.listen_port))
            
            # Socket for sending return data
            self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Start receiving thread
            self.running = True
            self.receiver_thread = threading.Thread(target=self.receive_game_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
            
            self.get_logger().info(f'UDP communication started on port {self.listen_port}')
            
        except Exception as e:
            self.get_logger().error(f'Failed to start UDP communication: {e}')
    
    def receive_game_data(self):
        """Thread function to receive game controller data"""
        while self.running and rclpy.ok():
            try:
                data, addr = self.receive_socket.recvfrom(1024)
                
                # Parse the received data
                game_data = self.parse_game_control_data(data)
                if game_data:
                    # Publish to ROS2
                    self.game_state_pub.publish(game_data)
                    
                    self.get_logger().debug(
                        f'Received game data: State={STATE_NAMES.get(game_data.state, "UNKNOWN")}, '
                        f'Time={game_data.secs_remaining}s'
                    )
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.get_logger().error(f'Error receiving game data: {e}')
    
    def parse_game_control_data(self, data: bytes) -> Optional[GameControlData]:
        """Parse binary game control data into ROS2 message"""
        try:
            if len(data) < 12:  # Minimum size check
                return None
            
            # Check header
            header = data[:4].decode('ascii')
            if header != GAMECONTROLLER_STRUCT_HEADER:
                return None
            
            # Parse basic game info
            offset = 4
            (version, packet_number, players_per_team, state, first_half,
             kick_off_team, secondary_state, drop_in_team, drop_in_time,
             secs_remaining, secondary_time) = struct.unpack_from(
                'BBBBBBBBBHHH', data, offset
            )
            offset += 11
            
            # Create ROS message
            msg = GameControlData()
            msg.header = header
            msg.version = version
            msg.packet_number = packet_number
            msg.players_per_team = players_per_team
            msg.state = state
            msg.first_half = first_half
            msg.kick_off_team = kick_off_team
            msg.secondary_state = secondary_state
            msg.drop_in_team = drop_in_team
            msg.drop_in_time = drop_in_time
            msg.secs_remaining = secs_remaining
            msg.secondary_time = secondary_time
            
            # Parse team data
            msg.teams = []
            for team_idx in range(2):
                team_info = self.parse_team_info(data, offset)
                if team_info:
                    msg.teams.append(team_info)
                    # Calculate team data size
                    team_size = 6 + SPL_COACH_MESSAGE_SIZE + 2 + (MAX_NUM_PLAYERS * 2)
                    offset += team_size
                else:
                    return None
            
            return msg
            
        except Exception as e:
            self.get_logger().error(f'Error parsing game data: {e}')
            return None
    
    def parse_team_info(self, data: bytes, offset: int) -> Optional[TeamInfo]:
        """Parse team information from binary data"""
        try:
            # Parse basic team info
            (team_number, team_colour, score, penalty_shot, 
             single_shots_low, single_shots_high) = struct.unpack_from('BBBBBB', data, offset)
            
            single_shots = single_shots_low | (single_shots_high << 8)
            offset += 6
            
            # Create team info message
            team_msg = TeamInfo()
            team_msg.team_number = team_number
            team_msg.team_colour = team_colour
            team_msg.score = score
            team_msg.penalty_shot = penalty_shot
            team_msg.single_shots = single_shots
            
            # Parse coach message
            team_msg.coach_message = list(data[offset:offset + SPL_COACH_MESSAGE_SIZE])
            offset += SPL_COACH_MESSAGE_SIZE
            
            # Parse coach info
            team_msg.coach = self.parse_robot_info(data, offset)
            offset += 2
            
            # Parse players info
            team_msg.players = []
            for i in range(MAX_NUM_PLAYERS):
                player_info = self.parse_robot_info(data, offset)
                team_msg.players.append(player_info)
                offset += 2
            
            return team_msg
            
        except Exception as e:
            self.get_logger().error(f'Error parsing team info: {e}')
            return None
    
    def parse_robot_info(self, data: bytes, offset: int) -> RobotInfo:
        """Parse robot information from binary data"""
        penalty, secs_till_unpenalised = struct.unpack_from('BB', data, offset)
        
        robot_msg = RobotInfo()
        robot_msg.penalty = penalty
        robot_msg.secs_till_unpenalised = secs_till_unpenalised
        
        return robot_msg
    
    def send_alive_message(self):
        """Send alive message to game controller"""
        if self.send_socket:
            try:
                return_data = GameControlReturnData()
                return_data.header = GAMECONTROLLER_RETURN_STRUCT_HEADER
                return_data.version = GAMECONTROLLER_RETURN_STRUCT_VERSION
                return_data.team = self.team_number
                return_data.player = self.player_number
                return_data.message = GAMECONTROLLER_RETURN_MSG_ALIVE
                
                # Convert to binary
                data = self.create_return_data_bytes(return_data)
                
                # Send to game controller
                self.send_socket.sendto(data, (self.gc_ip, GAMECONTROLLER_PORT))
                
                self.get_logger().debug(f'Sent alive message to {self.gc_ip}')
                
            except Exception as e:
                self.get_logger().error(f'Error sending alive message: {e}')
    
    def return_data_callback(self, msg: GameControlReturnData):
        """Handle return data messages from ROS2"""
        if self.send_socket:
            try:
                data = self.create_return_data_bytes(msg)
                self.send_socket.sendto(data, (self.gc_ip, GAMECONTROLLER_PORT))
                
                self.get_logger().info(
                    f'Sent return message: Team={msg.team}, Player={msg.player}, '
                    f'Message={msg.message}'
                )
                
            except Exception as e:
                self.get_logger().error(f'Error sending return data: {e}')
    
    def create_return_data_bytes(self, msg: GameControlReturnData) -> bytes:
        """Convert return data message to binary format"""
        header = msg.header.encode('ascii')[:4].ljust(4, b'\x00')
        data = header + struct.pack('BBBB', msg.version, msg.team, msg.player, msg.message)
        return data
    
    def destroy_node(self):
        """Clean up resources"""
        self.running = False
        
        if self.receiver_thread:
            self.receiver_thread.join(timeout=1.0)
        
        if self.receive_socket:
            self.receive_socket.close()
        
        if self.send_socket:
            self.send_socket.close()
        
        super().destroy_node()