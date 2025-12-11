#!/usr/bin/env python3

import rclpy
from std_msgs.msg import String
import sys
import threading
import time

class Op3CLIInterface:
    def __init__(self):
        rclpy.init()
        
        self.waiting_response = False
        self.node = rclpy.create_node('op3_cli_interface')
        self.cmd_pub = self.node.create_publisher(String, '/op3_rl_control/commands', 10)
        self.status_sub = self.node.create_subscription(
            String, 
            '/op3_rl_control/status', 
            self.status_callback, 
            10
        )
        
        self.ready = False
        
        print("🤖 OP3 RL Control - Command Line Interface")
        print("=" * 50)
        
    def status_callback(self, msg):
        """Receive status updates from control node"""
        if "READY" in msg.data:
            self.ready = True
            print(f"✅ {msg.data}")
            print("🎮 Ready for commands!")
        elif "JOINT_LIST:" in msg.data:
            print("\n📋 Available Joints:")
            lines = msg.data.split('\n')
            for line in lines[1:]:  # Skip the "JOINT_LIST:" header
                if line.strip():
                    print(line)
            print()
        elif msg.data.startswith("SUCCESS:"):
            print(f"🎉 {msg.data}")
        elif msg.data.startswith("ERROR:"):
            print(f"❌ {msg.data}")
        else:
            print(f"📡 {msg.data}")

        self.waiting_response = False

    def run(self):
        # Start ROS spinning in background thread
        spin_thread = threading.Thread(target=self._spin, daemon=True)
        spin_thread.start()
        
        self._wait_for_connection()
        self._show_help()
        self._main_loop()

    def _wait_for_connection(self):
        """Wait until connected to control node"""
        print("⏳ Connecting to OP3 control node", end="", flush=True)
        while not self.ready and rclpy.ok():
            print(".", end="", flush=True)
            time.sleep(0.5)
        print()  # New line after connection dots

    def _main_loop(self):
        """Main command processing loop"""
        try:
            while rclpy.ok():
                try:
                    command = self._get_user_input()
                    if not command:
                        continue
                    
                    if self._handle_exit_command(command):
                        break
                    elif self._handle_help_command(command):
                        continue
                    else:
                        self._process_command(command)
                        
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except EOFError:
                    break
                    
        finally:
            self.node.destroy_node()
            rclpy.shutdown()

    def _get_user_input(self):
        """Get input from user with proper waiting"""
        while self.waiting_response and rclpy.ok():
            time.sleep(0.1)
            
        return input("op3> ").strip()

    def _handle_exit_command(self, command):
        """Handle exit commands"""
        if command.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            return True
        return False

    def _handle_help_command(self, command):
        """Handle help commands"""
        if command.lower() in ['help', '?']:
            self._show_help()
            return True
        return False

    def _spin(self):
        """Background thread for ROS spinning"""
        try:
            rclpy.spin(self.node)
        except:
            pass

    def _send_command(self, command):
        """Send command to control node"""
        msg = String()
        msg.data = command
        self.cmd_pub.publish(msg)
        self.waiting_response = True

    def _process_command(self, command):
        """Process user commands"""
        if command.lower() == 'list':
            self._send_command('list')
        elif command.lower().startswith('set '):
            self._send_command(command)
        elif command.lower() in ['torque_on', 'torque_off']:
            self._send_command(command)
        elif command.lower().startswith('switch_mode '):
            self._send_command(command)
        elif command.lower() == 'all_to_zero':
            self._execute_all_to_zero()
        else:
            print("❌ Unknown command. Type 'help' for available commands.")

    def _execute_all_to_zero(self):
        """set all joints to 0 rad with 0.33 interval"""
        self._send_command('set head_pan 0.0')
        self._send_command('set head_tilt 0.0')
        time.sleep(0.33)
        
        self._send_command('set l_sho_pitch 0.0')
        self._send_command('set r_sho_pitch 0.0')
        self._send_command('set l_sho_roll 0.0')
        self._send_command('set r_sho_roll 0.0')
        time.sleep(0.33)
        
        self._send_command('set l_el 0.0')
        self._send_command('set r_el 0.0')
        self._send_command('set l_knee 0.0')
        self._send_command('set r_knee 0.0')
        time.sleep(0.33)
        
        self._send_command('set l_hip_pitch 0.0')
        self._send_command('set r_hip_pitch 0.0')
        self._send_command('set l_hip_roll 0.0')
        self._send_command('set r_hip_roll 0.0')
        time.sleep(0.33)
        
        self._send_command('set l_ank_pitch 0.0')
        self._send_command('set r_ank_pitch 0.0')
        self._send_command('set l_ank_roll 0.0')
        self._send_command('set r_ank_roll 0.0')

    def _show_help(self):
        """Show help message"""
        print("\n📖 Available Commands:")
        print("  list                    - Show all available joints")
        print("  set <joint> <angle>     - Set joint position (radians)")
        print("                           - <joint> can be index (0,1,2...) or name")
        print("                           - <joint> can be partial name (e.g., 'head' for head_pan)")
        print("  torque_on               - Enable torque (real robot modes only)")
        print("  torque_off              - Disable torque (real robot modes only)")
        print("  switch_mode <mode>      - Switch mode: sim | real | direct | simultaneous")
        print("  help, ?                 - Show this help message")
        print("  quit, exit, q           - Exit the program")
        print("\nExamples:")
        print("  set 0 1.57              - Set joint 0 (head_pan) to 1.57 radians")
        print("  set head_pan 0.0        - Set head_pan joint to 0.0")
        print("  set head 0.5            - Set all head joints (head_pan, head_tilt) to 0.5")
        print("  set l_ank 0.0           - Set all left ankle joints to 0.0")
        print("  torque_on               - Enable torque for real robot")
        print("  switch_mode real        - Switch to REAL mode (real robot only)")
        print("  switch_mode sim         - Switch to SIM mode (simulation only)")
        print("  switch_mode direct      - Switch to DIRECT mode (direct_control_module)")
        print("  switch_mode simultaneous- Control SIM and REAL at the same time")
        print()

def main():
    cli = Op3CLIInterface()
    cli.run()

if __name__ == '__main__':
    main()