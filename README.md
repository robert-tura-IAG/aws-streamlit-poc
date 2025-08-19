# ✈️ Aircraft Maintenance Insights Dashboard
## Overview
This project is a Streamlit-based web dashboard designed to provide real-time insights into aircraft maintenance data. It serves as a centralized interface for engineers, analysts, and operations teams to monitor, explore, and understand maintenance activities across fleets.

While future versions will incorporate predictive analytics, the current release emphasizes data availability, clarity, and actionable insights.

## 🔍 Features
Interactive Dashboard: Built with Streamlit for fast, responsive UI.
Maintenance Overview: Visual summaries of aircraft status, maintenance events, and operational readiness.
Filtering & Exploration: Drill down by aircraft type, maintenance category, or time range.
Insight Availability: Focused on surfacing key metrics and trends from historical and current data.
Auto-Start on EC2 Boot: Configured to launch automatically when the EC2 instance starts, ensuring availability at scheduled times.
## 🛠️ Tech Stack
Frontend: Streamlit
Backend: Python
Deployment: AWS EC2 with systemd service for auto-start
Data Source: CSV/Database (customizable)
## 🗂️ Project Sctructure
```
aws-streamlit-poc/
├── .gitignore
├── requirements.txt
├── README.md
├── streamlit_app.py         # Main Streamlit app entry point
├── src/                     # Source code (modules, utilities)
│   ├── __init__.py
│   ├── data_loader.py
│   └── plot_utils.py
├── config/                  # Configuration files (YAML, JSON, etc.)
│   └── app_config.yaml
├── assets/                  # Images, logos, static files
│   └── logo.png
└── .streamlit/              # Streamlit config files
    └── config.toml
```
## 🚀 Getting Started
### 1. Clone the Repository
```
git clone https://github.com/your-username/aws-streamlit-poc.git
cd aws-streamlit-poc
```
### 2. Set Up Virtual Environment
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the App
```
streamlit run Landing.py
```
