# 🚗 AI-Based Driving Pattern Monitoring & Range Estimation System for Electric Vehicles

<p align="center">
  <img src="https://img.shields.io/badge/Project-Final%20Year-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Domain-Electric%20Vehicles-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/Technology-AI%20%7C%20ML%20%7C%20IoT-orange?style=for-the-badge">
</p>

---

# 📌 Project Overview

This project focuses on developing an **AI-based driving pattern monitoring and EV range estimation system** capable of analyzing driver behaviour and estimating energy consumption in electric vehicles.

The system simulates an Electric Vehicle (EV) environment where driving parameters are monitored in real-time and processed using Artificial Intelligence techniques to classify driving behaviour into:

- 🟢 Eco Driving
- 🟡 Normal Driving
- 🔴 Aggressive Driving

Based on these driving patterns, the system estimates:
- ⚡ Energy Consumption
- 🔋 Battery Usage
- 🚘 Remaining Driving Range

---

# 🎯 Objectives

✅ Monitor driving behaviour in real-time  
✅ Simulate EV energy consumption  
✅ Classify driving patterns using AI/ML  
✅ Estimate remaining vehicle range  
✅ Promote energy-efficient driving habits  
✅ Integrate Embedded Systems with AI concepts  

---

# 🧠 Core Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main Programming |
| Streamlit | Interactive Dashboard |
| Machine Learning | Driving Pattern Classification |
| ESP32 | Data Acquisition (Planned Hardware) |
| Raspberry Pi | ML Processing (Planned Hardware) |
| Pandas & NumPy | Data Processing |
| Matplotlib | Data Visualization |

---

# ⚙️ System Workflow

```text
Driver Input (Throttle)
          ↓
Sensor Data Generation
          ↓
Driving Parameter Monitoring
          ↓
AI-Based Driving Pattern Detection
          ↓
Energy Consumption Estimation
          ↓
Remaining Range Prediction
```

---

# 📊 Features

✨ Interactive EV Dashboard  
✨ Real-time Driving Pattern Classification  
✨ Energy Consumption Monitoring  
✨ Battery Status Indicator  
✨ Driver Feedback System  
✨ Dynamic Range Estimation  
✨ Live Graph Visualization  

---

# 🖥️ Dashboard Preview

The dashboard simulates:
- Speed Monitoring
- Current Consumption
- AI Driving Classification
- Battery Percentage
- Estimated EV Range
- Driver Feedback Alerts

---

# 🔍 Driving Pattern Logic

| Driving Style | Condition |
|---|---|
| Eco | Low throttle & smooth driving |
| Normal | Moderate acceleration |
| Aggressive | High throttle & rapid acceleration |

---

# 🔋 Range Estimation Formula

```text
Range = Battery Capacity (Wh) / Energy Consumption (Wh/km)
```

The system dynamically estimates remaining EV range based on simulated driving conditions and power usage.

---

# 📁 Project Structure

```text
EV_AI_Project/
│
├── app.py
├── README.md
├── dataset/
├── ml_model/
├── hardware_docs/
└── presentation/
```

---

# 🚀 How to Run the Project

## 1️⃣ Install Dependencies

```bash
pip install streamlit pandas matplotlib scikit-learn
```

## 2️⃣ Run Streamlit App

```bash
streamlit run app.py
```

---

# 📚 Future Scope

🔹 Real-time hardware integration using ESP32  
🔹 Deployment on Raspberry Pi  
🔹 Real EV sensor integration  
🔹 Advanced Machine Learning models  
🔹 Cloud-based telemetry monitoring  
🔹 Mobile App Integration  

---

# 👨‍💻 Team Members

- Anurati Bhaduri
- Aritrika Chatterjee
- Abhinandan Sankar Sadhukhan
- Aditya Kumar Gupta
- Anindya Sundar Das

---

# 🎓 Academic Information

**Final Year B.Tech Project**  
Department of Electrical Engineering  
Academy of Technology  

---

# ⭐ Conclusion

This project demonstrates how Artificial Intelligence and Embedded Systems can be combined to develop intelligent EV monitoring systems capable of analyzing driving behaviour and estimating vehicle range in real time.

The project provides practical exposure to:
- Electric Vehicle Technology
- Embedded Systems
- Machine Learning
- Power Electronics
- Real-Time Monitoring Systems

---

# 🌟 Repository Highlights

✅ AI + EV Integration  
✅ Interactive Simulation  
✅ Real-Time Dashboard  
✅ Final Year Engineering Project  
✅ Streamlit-Based Visualization  

---

<p align="center">
  <b>⚡ Smart Driving Begins with Smart Monitoring ⚡</b>
</p>