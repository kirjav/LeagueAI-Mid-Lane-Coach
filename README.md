# 🧠 LeagueAI Mid Lane Coach

A League of Legends mid-lane analysis tool powered by match data and machine learning. This project builds a full data pipeline to evaluate midlane performance, identify areas of improvement, and ultimately help players win more games.

---

## 🚀 Key Features

- 🔎 Fetch ranked solo midlane match & timeline data via Riot API  
- 🧠 Extract lane-phase events like CS, roams, deaths, item timing, and more  
- 🔗 Merge and clean match/timeline data for analysis  
- 🧬 One-hot encode champion roles for modeling  
- 📊 Train ML models to predict win outcomes and highlight improvement areas  
- 🧠 Analyze your own matches to get tailored feedback

---

## 🛠️ Technology

- **Python** — Core programming language  
- **Pandas** — Data cleaning and manipulation  
- **scikit-learn** — ML training and encoding  
- **Joblib** — Save models and encoders  
- **Requests** — API interaction with Riot Games  
- **Riot API** — Match and timeline data  
- **Champion role mapping** — Custom one-hot encoding for champ roles  

---

### Sample Output Row

| match_id        | summoner       | champion | cs_at_10min | gold_diff_at_10 | early_roam | has_early_lane_prio | kda | opp_champion | win  |
|----------------|----------------|----------|-------------|------------------|------------|----------------------|-----|---------------|------|
| NA1_5280028785 | struggler#heed | Syndra   | 76          | 20               | FALSE      | FALSE                | 4.25| Yone          | FALSE |

---

## 📌 Future Plans

- SHAP or attention-based model explanations  
- Personalized improvement reports  
- Web dashboard or Discord bot integration  
- Expand features to include wave state, vision score, aggression index, etc.
