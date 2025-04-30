# LeagueAI-Mid-Lane-Coach

**An AI-powered coaching tool for League of Legends mid laners**, built to analyze Challenger-level replays and provide early-game decision feedback on roam and ward timing.

## 🎯 Project Goal

This MVP focuses on identifying and analyzing **key mid lane behaviors** — especially **roaming**, **vision control**, and **early deaths** — using parsed `.rofl` files from high-elo ranked matches. The goal is to emulate high-level decision-making and give actionable feedback for improvement.

---

## 💡 Key Features

- 🗺️ Extracts mid lane roam and ward timings from `.rofl` replay files
- 🧠 Compares decision timing against Challenger-level baselines
- 📊 Outputs structured features (e.g., `first_roam_time`, `ward_before_roam`, `cs_at_10min`)
- 🔍 Detects unsafe roams and missing vision before ganks
- ⚙️ Powered by Riot API, Python, and custom parsing logic

---

## 📁 Sample Output

| match_id     | summoner | first_ward_time | first_roam_time | ward_before_roam | roam_success | deaths_before_10min | cs_at_10min |
|--------------|----------|-----------------|------------------|------------------|--------------|---------------------|-------------|
| NA1_12345678 | Faker    | 03:10           | 05:32            | True             | True         | 0                   | 86          |

---

## 🔧 Tech Stack

- 🐍 **Python** — core data pipeline and replay parsing
- 📦 **requests** — Riot API integration
- 📊 **pandas**, **scikit-learn** — feature processing and basic modeling
- 💾 **CSV/JSON** — lightweight data storage
- 🖥️ **Streamlit** — for building a minimal UI

---

## 📌 Status
In progress!

