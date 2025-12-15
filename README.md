# 🚨 StreetGuardian AI

StreetGuardian AI is an AI-powered, voice-triggered emergency alert system designed for **public safety and social good**.

The system detects predefined emergency voice keywords and instantly triggers alerts with live visual evidence.

---

## 🎯 Problem Statement
In emergency situations, victims may not be able to unlock their phone or make a call to seek help.

---

## 💡 Solution
StreetGuardian AI enables **hands-free emergency alerts** using voice commands such as **HELP** or **POLICE**, allowing faster response in critical situations.

---

## ⚙️ System Overview
- Wake-word detection using Porcupine (Voice AI)
- Camera-based image capture using OpenCV
- Instant alerts sent to:
  - Android Mobile Application (Firebase Cloud Messaging)
  - Telegram (with captured snapshot)
- Local buzzer alert for nearby attention
- Fully standalone system with auto-start on boot

---

## 🧠 Technologies Used
- Python
- OpenCV
- Porcupine (Wake-word Detection)
- Raspberry Pi
- Firebase Cloud Messaging (FCM)
- Android (Kotlin)
- Telegram Bot API
- Linux (systemd)

---

## 🔧 Hardware Components
- Raspberry Pi
- USB Camera
- Microphone
- Buzzer
- Internet connectivity

---

## ▶️ Demo Video
A working demo of the physical prototype and alert system is available here:

🔗 **Demo Video: https://drive.google.com/file/d/1K81KrZylY7zTR3ZCY4YhclqvqL10HAIZ/view?usp=sharing

---

## 📸 Screenshots
Screenshots of the hardware setup and alert system are included in this repository.

---

## 🏆 Recognition
🏅 **Domain-Wise Best Team – AI for Social Good**  
HackVriksh 2025

---

## ⚠️ Important Note
This repository contains the **prototype and demo implementation** of StreetGuardian AI.

The final deployed Raspberry Pi system includes hardware-specific configurations and system-level services that are not included here.

This repository represents:
- Core system logic
- Voice-trigger workflow
- Camera capture
- Alert pipeline (Device → Cloud → Mobile)

---

## 🔐 Security Note
Sensitive credentials (API keys, Firebase service accounts) are **not included** in this repository for security reasons.

---

## 📌 License
This project is licensed under the MIT License.
