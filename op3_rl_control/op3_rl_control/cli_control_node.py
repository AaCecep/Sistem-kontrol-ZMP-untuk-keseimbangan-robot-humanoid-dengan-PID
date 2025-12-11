#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64, String, Bool
import sys


class Op3RlControlNode(Node):
    def __init__(self, mode):
        super().__init__("cli_control_node")

        # -----------------------------------------------------
        # MODE SELECTION
        # -----------------------------------------------------
        self.valid_modes = ["sim", "real", "direct", "simultaneous"]
        self.mode = mode.lower()
        if self.mode not in self.valid_modes:
            raise ValueError("Mode must be: sim | real | direct | simultaneous")

        self.get_logger().info(f"🚀 Starting OP3 control node in MODE = {self.mode.upper()}")

        # -----------------------------------------------------
        # OP3 Joint List (Unified)
        # -----------------------------------------------------
        self.joint_names = (
            'head_pan', 'head_tilt',
            'l_ank_pitch', 'l_ank_roll', 'l_el',
            'l_hip_pitch', 'l_hip_roll', 'l_hip_yaw',
            'l_knee', 'l_sho_pitch', 'l_sho_roll',
            'r_ank_pitch', 'r_ank_roll', 'r_el',
            'r_hip_pitch', 'r_hip_roll', 'r_hip_yaw',
            'r_knee', 'r_sho_pitch', 'r_sho_roll'
        )

        # -----------------------------------------------------
        # PUBLISHERS (always created; routing depends on mode)
        # -----------------------------------------------------
        # SIM (Webots) publishers
        self.joint_publishers = {}
        for joint in self.joint_names:
            topic = f"/robotis_op3/{joint}_position/command"
            self.joint_publishers[joint] = \
                self.create_publisher(Float64, topic, 10)
            self.get_logger().info(f"📢 (SIM) publisher: {topic}")

        # REAL (high-level controller) publishers
        self.real_pub = self.create_publisher(
            JointState, "/robotis/set_joint_states", 10
        )
        # Torque and module / controller control publishers
        self.torque_enable_pub = self.create_publisher(
            Bool, "/robotis/tuning_module/torque_enable", 10
        )
        self.enable_ctrl_module_pub = self.create_publisher(
            String, "/robotis/enable_ctrl_module", 10
        )
        self.get_logger().info("📢 (REAL) publisher: /robotis/set_joint_states")
        self.get_logger().info("📢 (REAL) publisher: /robotis/tuning_module/torque_enable")
        self.get_logger().info("📢 (REAL) publisher: /robotis/enable_ctrl_module")

        # DIRECT MODE (DirectControlModule) publisher
        self.direct_pub = self.create_publisher(
            JointState, "/robotis/direct_control/set_joint_states", 10
        )
        self.get_logger().info("📢 (DIRECT) publisher: /robotis/direct_control/set_joint_states")
        
        # -----------------------------------------------------
        # CLI communication
        # -----------------------------------------------------
        self.cmd_sub = self.create_subscription(
            String, "/op3_rl_control/commands", self.command_callback, 10
        )
        self.status_pub = self.create_publisher(String, "/op3_rl_control/status", 10)
        
        # APPLY INITIAL MODE
        self._switch_mode(self.mode)

        status = String()
        status.data = f"READY: Mode={self.mode.upper()} | Controlling {len(self.joint_names)} joints"
        self.status_pub.publish(status)

    # =========================================================
    # COMMAND HANDLING FROM CLI
    # =========================================================
    def command_callback(self, msg):
        self.process_command(msg.data.strip())

    def process_command(self, command):
        if command == "list":
            out = "JOINT_LIST:"
            for i, name in enumerate(self.joint_names):
                out += f"\n  {i}: {name}"
            self.status_pub.publish(String(data=out))
            return

        if command.startswith("set "):
            parts = command.split()
            if len(parts) != 3:
                self.status_pub.publish(String(data="ERROR: Usage: set <joint> <angle>"))
                return

            _, target, angle_str = parts

            try:
                angle = float(angle_str)
            except:
                self.status_pub.publish(String(data="ERROR: angle must be a float"))
                return

            names = self._resolve_joint_name(target)
            if not names:
                return

            for joint in names:
                self._send_joint_cmd(joint, angle)

            self.status_pub.publish(
                String(data=f"SUCCESS: Set {len(names)} joint(s) to {angle:.3f} rad")
            )
            return

        # NEW COMMANDS FOR REAL ROBOT CONTROL
        if command == "torque_on":
            self._enable_torque(True)
            return
            
        if command == "torque_off":
            self._enable_torque(False)
            return

        if command.startswith("switch_mode "):
            parts = command.split()
            if len(parts) != 2:
                self.status_pub.publish(String(data="ERROR: Usage: switch_mode <sim|real|direct|simultaneous>"))
                return
            new_mode = parts[1].lower()
            self._switch_mode(new_mode)
            return

        self.status_pub.publish(String(data="ERROR: Unknown command."))

    # =========================================================
    # TORQUE AND MODULE CONTROL
    # =========================================================
    def _enable_torque(self, enable):
        if self.mode not in ["real", "direct", "simultaneous"]:
            self.status_pub.publish(String(data=f"ERROR: torque control only available when controlling REAL robot (real|direct|simultaneous)"))
            return
            
        msg = Bool()
        msg.data = enable
        self.torque_enable_pub.publish(msg)
        state = "ON" if enable else "OFF"
        self.status_pub.publish(String(data=f"SUCCESS: Torque {state}"))

    def _enable_direct_control_module(self):
        if self.mode not in ["real", "simultaneous"]:
            self.status_pub.publish(String(data=f"ERROR: module control only available in REAL or SIMULTANEOUS mode"))
            return
            
        msg = String()
        msg.data = "direct_control_module"  # This enables the direct control module
        self.enable_ctrl_module_pub.publish(msg)
        self.status_pub.publish(String(data="SUCCESS: Direct Control Module enabled"))

    def _switch_mode(self, new_mode):
        """Switch internal control mode and adjust controller modules when applicable."""
        if new_mode not in self.valid_modes:
            self.status_pub.publish(
                String(data=f"ERROR: invalid mode '{new_mode}'. Valid: sim | real | direct | simultaneous")
            )
            return

        self.mode = new_mode

        # Try to adjust controller modules on the real robot side
        # - direct: enable DirectControlModule
        # - real / simultaneous: disable motion modules (set to 'none') for direct joint control
        # - sim: no real robot control required
        if self.mode == "direct":
            msg = String()
            msg.data = "direct_control_module"
            self.enable_ctrl_module_pub.publish(msg)
            self.status_pub.publish(String(data="SUCCESS: Switched to DIRECT mode (direct_control_module enabled)"))
        elif self.mode in ["real", "simultaneous"]:
            msg = String()
            msg.data = "none"
            self.enable_ctrl_module_pub.publish(msg)
            self.status_pub.publish(String(data=f"SUCCESS: Switched to {self.mode.upper()} mode (motion modules disabled)"))
        else:  # sim
            self.status_pub.publish(String(data="SUCCESS: Switched to SIM mode (simulation only)"))

    # =========================================================
    # SENDING JOINT COMMANDS (SIM / REAL / DIRECT)
    # =========================================================
    def _send_joint_cmd(self, joint, angle):
        # In SIMULTANEOUS mode, send to both SIM and REAL topics.
        if self.mode in ["sim", "simultaneous"]:
            msg = Float64()
            msg.data = angle
            self.joint_publishers[joint].publish(msg)

        if self.mode in ["real", "simultaneous"]:
            msg = JointState()
            msg.name = [joint]
            msg.position = [angle]
            self.real_pub.publish(msg)

        if self.mode == "direct":
            msg = JointState()
            msg.name = [joint]
            msg.position = [angle]
            self.direct_pub.publish(msg)

    # =========================================================
    # JOINT NAME RESOLUTION (index / exact / partial match)
    # =========================================================
    def _resolve_joint_name(self, target):
        # index?
        try:
            idx = int(target)
            if 0 <= idx < len(self.joint_names):
                return [self.joint_names[idx]]
            else:
                self.status_pub.publish(String(data="ERROR: index out of range"))
                return None
        except:
            pass

        # exact name?
        if target in self.joint_names:
            return [target]

        # partial match
        matches = [name for name in self.joint_names if target.lower() in name.lower()]
        if matches:
            return matches

        self.status_pub.publish(String(data=f"ERROR: joint '{target}' not found"))
        return None


def main(args=None):
    rclpy.init(args=args)
    mode = "sim"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    node = Op3RlControlNode(mode)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()