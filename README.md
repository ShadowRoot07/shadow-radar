# 🛡️ Shadow Radar

**Shadow Radar** is an automated lead-generation tool designed to help mental health professionals find people in need of help across social platforms like Reddit. 

This project was specifically built to assist a psychologist in identifying Spanish-speaking users who are expressing emotional distress or explicitly seeking therapy.

## 🚀 How it Works
1. **Scanning**: The bot crawls specific subreddits (e.g., `r/desahogo`, `r/psicologia`) using web scraping.
2. **Analysis**: It sends the post content to **Google Gemini AI** to determine if the user is a potential patient.
3. **Delivery**: If a high-potential lead is found, the bot generates a professional report (Embed) and sends it to a private **Discord** channel.

## 🛠️ Tech Stack
- **Language:** Python 3.13
- **Environment:** Termux (Development) & GitHub Actions (Production)
- **AI:** Google Generative AI (Gemini 1.5 Flash)
- **Interface:** Discord.py
- **Scraping:** HTTPX (Asynchronous)

## ⚙️ Deployment
This project runs as a **Persistent Worker** using GitHub Actions. It is scheduled to run every 30 minutes to ensure real-time monitoring without consuming local hardware resources.

## 👤 Developer
Developed by **ShadowRoot07**. 
*"Navigating the shadows of the internet to bring light to those in need."*

---
*Disclaimer: This tool is intended for professional use only. It identifies public posts and does not automate messaging, ensuring that the final contact is always human and ethical.*

