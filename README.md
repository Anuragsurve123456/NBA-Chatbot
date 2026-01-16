# 🏀 NBA Intelligent Chatbot (AWS Serverless)

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AWS](https://img.shields.io/badge/AWS-Serverless-orange)
![Bedrock](https://img.shields.io/badge/AWS-Bedrock-purple)
![Status](https://img.shields.io/badge/Project-Completed-success)
![Focus](https://img.shields.io/badge/Focus-Cloud%20Computing%20%26%20AI-blueviolet)

**Authors:**  
- Anurag Surve
- Vishal Fulsundar  
- Omoniyi Israel    

**Domain:** Cloud Computing · Serverless Architecture · AI Systems · Sports Analytics  
**Course:** Cloud Computing (Fall 2025)  
**University:** George Washington University  

---

## 🔍 Project Snapshot (TL;DR)

This project implements an **intelligent NBA chatbot** that answers **natural-language basketball questions** using a **fully serverless AWS architecture**.

Users can ask questions about **players, teams, standings, games, and rosters**, and receive **real-time, human-like responses** powered by **AWS Bedrock** and **live NBA data from API-Sports**.

The project emphasizes **end-to-end cloud system design**, including API Gateway routing, Lambda orchestration, external API integration, and LLM-based intent understanding.

---

## 🎯 Objectives

- Build a cloud-native NBA chatbot using AWS serverless services  
- Support natural-language NBA queries  
- Fetch real-time NBA statistics  
- Use AWS Bedrock to understand intent and generate responses  
- Demonstrate a scalable and modular serverless architecture  

---

## 🧠 System Overview

The chatbot follows a multi-service serverless workflow:

1. Users interact with a Streamlit web application  
2. Requests are routed through AWS API Gateway  
3. A Chat Lambda uses AWS Bedrock to:
   - Understand user intent  
   - Extract entities such as players, teams, and seasons  
4. A Stats Lambda fetches live NBA data from API-Sports  
5. Data is normalized and returned to the Chat Lambda  
6. Bedrock generates a natural-language response  
7. The final answer is displayed in the chat interface  

This design cleanly separates **UI**, **reasoning**, and **data retrieval**.

---

## 🏗 Architecture

**Core Components:**
- Streamlit – Chat-based frontend UI  
- AWS API Gateway – HTTP routing layer  
- AWS Lambda (Chat) – Intent detection and response generation  
- AWS Lambda (Stats) – NBA data retrieval and normalization  
- AWS Bedrock – Large Language Model (Claude 3 Haiku)  
- API-Sports NBA API – Live basketball statistics  
- Lambda Layer – Shared dependencies  

The architecture is fully serverless, scalable, and cost-efficient.

---

## 🔄 API Routes

All routes are exposed under the `/nba` base path:

| Route | Purpose |
|------|--------|
| `/chat` | Natural-language chat endpoint |
| `/team-stats` | Team statistics |
| `/player-stats` | Player statistics |
| `/team-roster` | Team rosters |
| `/games` | Game data |
| `/standings` | League standings |

---

## 🧪 Example Queries

- “Give me Stephen Curry’s stats this season”  
- “Who is on the Oklahoma City Thunder roster?”  
- “Show me the NBA standings”  
- “How did the Lakers perform last season?”  

---

## 🛠 Tech Stack

**Languages & Frameworks**
- Python  
- Streamlit  

**Cloud & AI**
- AWS Lambda  
- AWS API Gateway  
- AWS Bedrock (Claude 3 Haiku)  

**Data & APIs**
- API-Sports (NBA)  
- RESTful APIs  

---

## ▶️ Running the App Locally

```bash
pip install -r requirements.txt
streamlit run app.py
