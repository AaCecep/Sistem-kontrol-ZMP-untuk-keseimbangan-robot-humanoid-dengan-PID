# 🦿 ZMP-Based PID Control for Humanoid Robot Balance  
### (ROBOTIS OP3 – Bachelor Thesis Project)
![image_alt](https://github.com/AaCecep/Sistem-kontrol-ZMP-untuk-keseimbangan-robot-humanoid-dengan-PID/blob/b9e12c89ccac61a0afcc4de799b1210ae31ce51d/Screenshot%202026-02-14%20074559.png?raw=true)
---

## 📌 Overview
This project implements a **Zero Moment Point (ZMP)-based PID Control System** to enhance the dynamic stability of the humanoid robot ROBOTIS OP3.

The system maintains the ZMP position within the Support Polygon during walking motion, including obstacle scenarios such as inclines and declines.

This research was conducted as a Bachelor Thesis in Computer Engineering, Faculty of Computer Science, Universitas Brawijaya (2025).

---

## 🎯 Research Objectives
- Implement real-time **Center of Mass (CoM)** calculation  
- Implement real-time **Zero Moment Point (ZMP)** estimation  
- Apply **Low Pass Filter** to reduce IMU noise  
- Design and tune **PID Controller (Ziegler-Nichols method)**  
- Compare performance of **P, PI, and PID controllers**  
- Improve walking stability under dynamic conditions  

---

## 🏗 System Architecture

### 🔹 Sensor Input
- IMU (Inertial Measurement Unit)
- Joint State Servo Feedback

### 🔹 Processing Pipeline
1. CoM Calculation  
2. ZMP Calculation  
3. Low Pass Filtering  
4. Error Computation (ZMP_actual – ZMP_setpoint)  
5. PID Control  
6. Gait Parameter Adjustment
7. Inverse Kinematics  
8. Walking Execution  

---

## ⚙️ Hardware Specifications
- ROBOTIS OP3 Humanoid Robot (20 DoF)  
- Intel NUC7i3BNK  
- OpenCR 1.0  
- Dynamixel XM430-W350-R Servo  
- LiPo 4S 14.8V Battery  

---

## 🧠 Control Strategy
![image_alt](https://github.com/AaCecep/Sistem-kontrol-ZMP-untuk-keseimbangan-robot-humanoid-dengan-PID/blob/8ff98ad9f05215df12b0d81460dcabc6f074a1a1/Screenshot%202026-02-14%20074624.png?raw=true)
### 🔹 PID-Based ZMP Control Architecture

The block diagram above illustrates the closed-loop control system used to maintain humanoid robot stability based on Zero Moment Point (ZMP).

#### 1️⃣ Set Point
The desired stability condition is defined as:
ZMP_x = 0


This represents the ideal ZMP position at the center of the support polygon to maintain balance.

---

#### 2️⃣ Error Computation

The system computes the control error as:

e(t) = ZMP_actual - ZMP_setpoint


This error represents the deviation of the robot's dynamic stability from the desired condition.

---

#### 3️⃣ PID Controller

The error is processed by a PID controller consisting of:

- **Proportional (Kp·e(t))** → Reacts to present error  
- **Integral (Ki∫e(t)dt)** → Eliminates steady-state error  
- **Derivative (Kd·de(t)/dt)** → Predicts future error trend  

The total controller output is:

u(t) = Kp·e(t) + Ki∫e(t)dt + Kd·de(t)/dt


This output generates an `x_offset` correction signal.

---

#### 4️⃣ Walking Gait Adjustment

The `x_offset` modifies the walking gait parameter (`init_x_offset`), shifting the robot's center of mass to counteract instability.

---

#### 5️⃣ Inverse Kinematics

The adjusted gait parameters are passed to the inverse kinematics module, which computes the required joint angles:

θ_ankle_pitch

These joint commands are then sent to the actuators.

---

#### 6️⃣ Feedback Loop

The robot's actual ZMP is measured using IMU and joint state data.

To reduce sensor noise, the signal is processed through a **Low Pass Filter** before being fed back into the controller.

This forms a **closed-loop feedback control system**, continuously correcting posture in real-time.

---

### 🔁 Control System Summary

The architecture forms a real-time closed-loop stabilization system:


## 🎥 Demo Videos

📁 **Full Demo Folder:**  
https://drive.google.com/drive/folders/1HNzw77H0mEAN7rJq44KuiGXcWjupy2Me
