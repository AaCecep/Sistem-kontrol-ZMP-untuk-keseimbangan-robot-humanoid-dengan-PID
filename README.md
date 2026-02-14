# 🦿 ZMP-Based PID Control for Humanoid Robot Balance  
### (ROBOTIS OP3 – Bachelor Thesis Project)
![image_alt](https://github.com/AaCecep/Sistem-kontrol-ZMP-untuk-keseimbangan-robot-humanoid-dengan-PID/blob/96d9186de627417ce31a07605a980e8b74845b86/Diagram%20Blok%20Sistem%20Kontrol%20Keseimbangan%20PID.drawio.png?raw=true)
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
6. Gait Parameter Adjustment (`init_x_offset`)  
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

### 🔹 Zero Moment Point (ZMP)
Robot stability is achieved when the ZMP remains inside the Support Polygon area.

### 🔹 PID Controller
The PID controller corrects walking posture based on ZMP error:

