import socket
import struct
import threading
from typing import Optional

import rclpy
from rclpy.node import Node

# Constants
GAMECONTROLLER_PORT = 3838
GAMECONTROLLER_STRUCT_HEADER = "RGme"
GAMECONTROLLER_STRUCT_VERSION = 8
MAX_NUM_PLAYERS = 11

# Team colors
TEAM_BLUE = 0
TEAM_CYAN = 0
TEAM_RED = 1
TEAM_MAGENTA = 1
DROPBALL = 2

# Game states
STATE_INITIAL = 0
STATE_READY = 1
STATE_SET = 2
STATE_PLAYING = 3
STATE_FINISHED = 4

# Secondary states
STATE2_NORMAL = 0
STATE2_PENALTYSHOOT = 1
STATE2_OVERTIME = 2
STATE2_TIMEOUT = 3

# Penalties
PENALTY_NONE = 0
PENALTY_SPL_BALL_HOLDING = 1
PENALTY_SPL_PLAYER_PUSHING = 2
PENALTY_SPL_OBSTRUCTION = 3
PENALTY_SPL_INACTIVE_PLAYER = 4
PENALTY_SPL_ILLEGAL_DEFENDER = 5
PENALTY_SPL_LEAVING_THE_FIELD = 6
PENALTY_SPL_PLAYING_WITH_HANDS = 7
PENALTY_SPL_REQUEST_FOR_PICKUP = 8
PENALTY_SPL_COACH_MOTION = 9

# Return message types
GAMECONTROLLER_RETURN_STRUCT_HEADER = "RGrt"
GAMECONTROLLER_RETURN_STRUCT_VERSION = 2
GAMECONTROLLER_RETURN_MSG_MAN_PENALISE = 0
GAMECONTROLLER_RETURN_MSG_MAN_UNPENALISE = 1
GAMECONTROLLER_RETURN_MSG_ALIVE = 2

SPL_COACH_MESSAGE_SIZE = 40

# State name mappings
STATE_NAMES = {
    STATE_INITIAL: "INITIAL",
    STATE_READY: "READY",
    STATE_SET: "SET", 
    STATE_PLAYING: "PLAYING",
    STATE_FINISHED: "FINISHED"
}

PENALTY_NAMES = {
    PENALTY_NONE: "NONE",
    PENALTY_SPL_BALL_HOLDING: "BALL_HOLDING",
    PENALTY_SPL_PLAYER_PUSHING: "PLAYER_PUSHING",
    PENALTY_SPL_OBSTRUCTION: "OBSTRUCTION",
    PENALTY_SPL_INACTIVE_PLAYER: "INACTIVE_PLAYER",
    PENALTY_SPL_ILLEGAL_DEFENDER: "ILLEGAL_DEFENDER",
    PENALTY_SPL_LEAVING_THE_FIELD: "LEAVING_THE_FIELD",
    PENALTY_SPL_PLAYING_WITH_HANDS: "PLAYING_WITH_HANDS",
    PENALTY_SPL_REQUEST_FOR_PICKUP: "REQUEST_FOR_PICKUP",
    PENALTY_SPL_COACH_MOTION: "COACH_MOTION"
}

TEAM_COLOR_NAMES = {
    TEAM_BLUE: "BLUE",
    TEAM_RED: "RED"
}

class RobotInfo:
    def __init__(self):
        self.penalty = 0
        self.secs_till_unpenalised = 0

class TeamInfo:
    def __init__(self):
        self.team_number = 0
        self.team_colour = 0
        self.score = 0
        self.penalty_shot = 0
        self.single_shots = 0
        self.coach_message = b''
        self.coach = RobotInfo()
        self.players = [RobotInfo() for _ in range(MAX_NUM_PLAYERS)]

class GameControlData:
    def __init__(self):
        self.header = ""
        self.version = 0
        self.packet_number = 0
        self.players_per_team = 0
        self.state = 0
        self.first_half = 0
        self.kick_off_team = 0
        self.secondary_state = 0
        self.drop_in_team = 0
        self.drop_in_time = 0
        self.secs_remaining = 0
        self.secondary_time = 0
        self.teams = [TeamInfo(), TeamInfo()]


class SimpleGameControllerNode(Node):
    """Simple ROS2 Node for RoboCup Game Controller communication - Print only"""
    
    def __init__(self):
        super().__init__('simple_robocup_game_controller')
        
        # Parameters
        self.declare_parameter('team_number', 1)
        self.declare_parameter('player_number', 1)
        self.declare_parameter('gamecontroller_ip', '255.255.255.255')
        self.declare_parameter('listen_port', GAMECONTROLLER_PORT)
        self.declare_parameter('send_alive_interval', 2.0)
        self.declare_parameter('verbose', True)
        
        self.team_number = self.get_parameter('team_number').value
        self.player_number = self.get_parameter('player_number').value
        self.gc_ip = self.get_parameter('gamecontroller_ip').value
        self.listen_port = self.get_parameter('listen_port').value
        self.alive_interval = self.get_parameter('send_alive_interval').value
        self.verbose = self.get_parameter('verbose').value
        
        # UDP socket for receiving game controller data
        self.receive_socket = None
        self.send_socket = None
        self.receiver_thread = None
        self.running = False
        
        # Last game state for change detection
        self.last_state = None
        self.last_secs_remaining = None
        self.last_scores = [None, None]
        
        # Timer for sending alive messages
        self.alive_timer = self.create_timer(
            self.alive_interval, 
            self.send_alive_message
        )
        
        self.get_logger().info('='*60)
        self.get_logger().info('🤖 RoboCup Game Controller Node Started')
        self.get_logger().info(f'📋 Team: {self.team_number}, Player: {self.player_number}')
        self.get_logger().info(f'🌐 GameController IP: {self.gc_ip}')
        self.get_logger().info(f'🔊 Listen Port: {self.listen_port}')
        self.get_logger().info('='*60)
        
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
            
            self.get_logger().info(f'✅ UDP communication started on port {self.listen_port}')
            
        except Exception as e:
            self.get_logger().error(f'❌ Failed to start UDP communication: {e}')
    
    def receive_game_data(self):
        """Thread function to receive game controller data"""
        while self.running and rclpy.ok():
            try:
                data, addr = self.receive_socket.recvfrom(1024)

                self.get_logger().warn(f"Received {len(data)} bytes from {addr}, header={data[:4]}")
                
                # Parse the received data
                game_data = self.parse_game_control_data(data)
                if game_data:
                    self.display_game_data(game_data, addr)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.get_logger().error(f'❌ Error receiving game data: {e}')
    
    def parse_game_control_data(self, data: bytes) -> Optional[GameControlData]:
        """Parse binary game control data"""
        try:
            if len(data) < 12:  # Minimum size check
                return None

            # Check header
            header = data[:4].decode('ascii', errors='ignore')
            if header != GAMECONTROLLER_STRUCT_HEADER:
                return None

            # --- Parse basic game info ---
            offset = 4  # mulai setelah header
            fmt = 'BBBBBBBBBHHH'
            expected_size = struct.calcsize(fmt)

            if len(data) < offset + expected_size:
                self.get_logger().warn(f"⚠️ Packet too small for game info, got {len(data)} bytes")
                return None

            (version, packet_number, players_per_team, state, first_half,
            kick_off_team, secondary_state, drop_in_team, drop_in_time,
            secs_remaining, secondary_time, _) = struct.unpack_from(fmt, data, offset)

            offset += expected_size  # pastikan offset bergeser sesuai ukuran struct

            # Buat game_data object
            game_data = GameControlData()
            game_data.header = header
            game_data.version = version
            game_data.packet_number = packet_number
            game_data.players_per_team = players_per_team
            game_data.state = state
            game_data.first_half = first_half
            game_data.kick_off_team = kick_off_team
            game_data.secondary_state = secondary_state
            game_data.drop_in_team = drop_in_team
            game_data.drop_in_time = drop_in_time
            game_data.secs_remaining = secs_remaining
            game_data.secondary_time = secondary_time

            # --- Parse team data ---
            for team_idx in range(2):
                team_info, offset = self.parse_team_info(data, offset)
                if team_info:
                    game_data.teams[team_idx] = team_info
                else:
                    return None

            return game_data

        except Exception as e:
            self.get_logger().error(f'❌ Error parsing game data: {e}')
            return None

    def parse_team_info(self, data: bytes, offset: int) -> (Optional[TeamInfo], int):
        """Parse team information from binary data"""
        try:
            start_offset = offset

            # Basic team info (6 bytes)
            if len(data) < offset + 6:
                return None, start_offset
            (team_number, team_colour, score, penalty_shot,
            single_shots_low, single_shots_high) = struct.unpack_from('BBBBBB', data, offset)
            single_shots = single_shots_low | (single_shots_high << 8)
            offset += 6

            team_info = TeamInfo()
            team_info.team_number = team_number
            team_info.team_colour = team_colour
            team_info.score = score
            team_info.penalty_shot = penalty_shot
            team_info.single_shots = single_shots

            # Coach message
            if len(data) < offset + SPL_COACH_MESSAGE_SIZE:
                return None, start_offset
            team_info.coach_message = data[offset:offset + SPL_COACH_MESSAGE_SIZE]
            offset += SPL_COACH_MESSAGE_SIZE

            # Coach info (2 bytes)
            if len(data) < offset + 2:
                return None, start_offset
            team_info.coach = self.parse_robot_info(data, offset)
            offset += 2

            # Players info (2 * MAX_NUM_PLAYERS bytes)
            for i in range(MAX_NUM_PLAYERS):
                if len(data) < offset + 2:
                    return None, start_offset
                team_info.players[i] = self.parse_robot_info(data, offset)
                offset += 2

            return team_info, offset

        except Exception as e:
            self.get_logger().error(f'❌ Error parsing team info: {e}')
            return None, offset


    def parse_robot_info(self, data: bytes, offset: int) -> RobotInfo:
        """Parse robot information from binary data"""
        penalty, secs_till_unpenalised = struct.unpack_from('BB', data, offset)
        
        robot_info = RobotInfo()
        robot_info.penalty = penalty
        robot_info.secs_till_unpenalised = secs_till_unpenalised
        
        return robot_info
    
    def display_game_data(self, game_data: GameControlData, addr):
        """Display game data in a formatted way"""
        state_changed = self.last_state != game_data.state
        time_changed = self.last_secs_remaining != game_data.secs_remaining
        score_changed = (self.last_scores[0] != game_data.teams[0].score or 
                        self.last_scores[1] != game_data.teams[1].score)
        
        # Always show important changes
        if state_changed or score_changed:
            self.get_logger().info('='*80)
            self.print_game_status(game_data, addr)
            self.print_team_info(game_data)
            self.check_penalties(game_data)
            self.get_logger().info('='*80)
        # Show time updates if verbose or every 10 seconds
        elif time_changed and (self.verbose or game_data.secs_remaining % 10 == 0):
            self.print_game_status(game_data, addr)
        
        # Update last state
        self.last_state = game_data.state
        self.last_secs_remaining = game_data.secs_remaining
        self.last_scores = [game_data.teams[0].score, game_data.teams[1].score]
    
    def print_game_status(self, game_data: GameControlData, addr):
        """Print current game status"""
        state_name = STATE_NAMES.get(game_data.state, f"UNKNOWN({game_data.state})")
        half_name = "1st Half" if game_data.first_half else "2nd Half"
        
        # Format time
        mins = game_data.secs_remaining // 60
        secs = game_data.secs_remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Kick off team
        kickoff_team = TEAM_COLOR_NAMES.get(game_data.kick_off_team, f"TEAM_{game_data.kick_off_team}")
        
        self.get_logger().info(
            f'🎮 GAME STATUS | {state_name} | {half_name} | '
            f'Time: {time_str} | Kickoff: {kickoff_team} | '
            f'From: {addr[0]}'
        )
    
    def print_team_info(self, game_data: GameControlData):
        """Print team information"""
        for i, team in enumerate(game_data.teams):
            color_name = TEAM_COLOR_NAMES.get(team.team_colour, f"COLOR_{team.team_colour}")
            
            self.get_logger().info(
                f'🏆 Team {team.team_number} ({color_name}) | '
                f'Score: {team.score} | '
                f'Penalty Shots: {team.penalty_shot}'
            )
    
    def check_penalties(self, game_data: GameControlData):
        """Check and display player penalties"""
        for team_idx, team in enumerate(game_data.teams):
            # Check coach penalty
            if team.coach.penalty != PENALTY_NONE:
                penalty_name = PENALTY_NAMES.get(team.coach.penalty, f"PENALTY_{team.coach.penalty}")
                self.get_logger().warn(
                    f'⚠️  Team {team.team_number} COACH: {penalty_name} '
                    f'({team.coach.secs_till_unpenalised}s remaining)'
                )
            
            # Check player penalties
            for player_idx, player in enumerate(team.players):
                if player.penalty != PENALTY_NONE:
                    penalty_name = PENALTY_NAMES.get(player.penalty, f"PENALTY_{player.penalty}")
                    self.get_logger().warn(
                        f'⚠️  Team {team.team_number} Player {player_idx + 1}: {penalty_name} '
                        f'({player.secs_till_unpenalised}s remaining)'
                    )
    
    def send_alive_message(self):
        """Send alive message to game controller"""
        if self.send_socket:
            try:
                # Create return data
                header = GAMECONTROLLER_RETURN_STRUCT_HEADER.encode('ascii')[:4].ljust(4, b'\x00')
                data = header + struct.pack('BBBB', 
                                          GAMECONTROLLER_RETURN_STRUCT_VERSION,
                                          self.team_number, 
                                          self.player_number, 
                                          GAMECONTROLLER_RETURN_MSG_ALIVE)
                
                # Send to game controller
                self.send_socket.sendto(data, (self.gc_ip, GAMECONTROLLER_PORT))
                
                if self.verbose:
                    self.get_logger().debug(f'💓 Sent alive message to {self.gc_ip}')
                
            except Exception as e:
                self.get_logger().error(f'❌ Error sending alive message: {e}')
    
    def destroy_node(self):
        """Clean up resources"""
        self.get_logger().info('🛑 Shutting down GameController Node...')
        
        self.running = False
        
        if self.receiver_thread:
            self.receiver_thread.join(timeout=1.0)
        
        if self.receive_socket:
            self.receive_socket.close()
        
        if self.send_socket:
            self.send_socket.close()
        
        self.get_logger().info('✅ GameController Node shut down complete')
        super().destroy_node()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    node = SimpleGameControllerNode()
    
    try:
        print("\n" + "="*80)
        print("🤖 RoboCup Game Controller Monitor")
        print("📡 Listening for game controller data...")
        print("💡 Use Ctrl+C to stop")
        print("="*80 + "\n")
        
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        print("\n🛑 Received Ctrl+C, shutting down...")
    except Exception as e:
        node.get_logger().error(f'❌ Unexpected error: {e}')
    finally:
        node.destroy_node()
        rclpy.shutdown()
        print("👋 Goodbye!")


if __name__ == '__main__':
    main()