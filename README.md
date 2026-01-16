# 🏀 NBA Intelligent Chatbot (AWS & API-Sports)

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Bedrock](https://img.shields.io/badge/AWS-Bedrock-purple)
![Status](https://img.shields.io/badge/Project-Inactive-lightgrey)
![Focus](https://img.shields.io/badge/Focus-Cloud%20Computing%20%26%20AI-blueviolet)

**Authors:**  
- Vishal Fulsundar  
- Omoniyi Israel  
- Anurag Surve  

**Domain:** Cloud Computing · AI Systems · Sports Analytics  
**Course:** Cloud Computing (Fall 2025)  
**University:** George Washington University  

---

## 🔍 Project Snapshot (TL;DR)

This project implements an **intelligent NBA chatbot** designed to answer **natural-language basketball questions** using **AWS cloud services**, **AWS Bedrock**, and **live NBA data from API-Sports**.

The system was built to demonstrate **cloud-based AI system design**, including API Gateway routing, Lambda-based processing, external API integration, and LLM-driven intent understanding.  
The application is **currently inactive** but fully functional from a system and architectural standpoint.

---

## 🎯 Objectives

- Design an intelligent NBA chatbot using AWS cloud services  
- Support natural-language NBA queries  
- Retrieve real-time NBA statistics from an external API  
- Use AWS Bedrock for intent understanding and response generation  
- Demonstrate modular cloud application architecture  

---

## 🧠 System Overview

The chatbot follows a cloud-based workflow:

1. Users interact with a Streamlit web application  
2. Requests are sent to AWS API Gateway  
3. A Chat processing component uses AWS Bedrock to:
   - Understand user intent  
   - Extract entities such as players, teams, and seasons  
4. A statistics processing component retrieves NBA data from API-Sports  
5. Retrieved data is normalized and combined with AI-generated explanations  
6. The final response is returned to the frontend interface  

The design separates **user interaction**, **AI reasoning**, and **data retrieval** for clarity and maintainability.

---

## 🏗 Architecture

**Core Components:**
- Streamlit – Chat-based frontend UI  
- AWS API Gateway – Request routing  
- AWS Lambda – Backend processing logic  
- AWS Bedrock – Large Language Model (Claude 3 Haiku)  
- API-Sports NBA API – Live basketball statistics  
- Lambda Layer – Shared dependencies  

The architecture emphasizes **scalability, modularity, and clarity**, rather than continuous deployment.

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
- AWS API Gateway  
- AWS Lambda  
- AWS Bedrock (Claude 3 Haiku)  

**Data & APIs**
- API-Sports (NBA)  
- RESTful APIs  

---

## ▶️ Running the App Locally

```bash
pip install -r requirements.txt
streamlit run app.py
