# 🛰️ Shadow Radar

**Shadow Radar** is an automated, AI-driven monitoring system designed to identify high-impact social and psychological situations across Reddit. Originally conceived to assist mental health professionals, the radar has evolved into a multi-category tool that detects emotional crises, asylum/migration needs, sports psychology opportunities, and vocational guidance requests.

*"Navigating the shadows of the internet to bring light to those in need."*

## 🌟 Key Features
- **Specialized Detection**: Scans for specific scenarios including Asylum/Migration psychological support, Sports Performance, and Vocational Orientation.
- **AI-Driven Analysis**: Leverages **Groq Cloud** LLMs (Llama 3.1/3.3) for high-speed, professional-grade text categorization.
- **Resilient Architecture**: Implements a self-healing model discovery algorithm that automatically switches between AI models if one is decommissioned or hit by rate limits.
- **Automated Patrolling**: Operates as a persistent worker on **GitHub Actions**, running every 8 hours to provide balanced, comprehensive coverage.
- **Async Efficiency**: Built with `httpx` and `asyncio` for non-blocking, high-performance data scraping and delivery.

## 🛠️ Tech Stack
- **Engine:** Python 3.11+
- **Dev Environment:** Termux (Full mobile development workflow)
- **CI/CD & Hosting:** GitHub Actions
- **AI Infrastructure:** Groq Cloud (Llama 3.3-70b / Llama 3.1-8b)
- **Interface:** Discord.py
- **Reliability:** Pytest with Async Mocking for API and Scraper stability

## 🚀 How it Works
1. **Scanning**: The bot patrols targeted subreddits (e.g., `r/desahogo`, `r/DerechoGenial`) using a stealthy RSS-based scraping technique.
2. **Filtering**: It processes posts from the last ~8 hours (400 mins) to ensure no critical information is missed between cycles.
3. **AI Evaluation**: Content is sent to the **Groq fallback engine**, which categorizes the post into specialized buckets (Asylum, Crisis, Sports, etc.).
4. **Delivery**: High-relevance findings are summarized in Spanish and delivered to a private **Discord** channel with direct links for human intervention.

## 🧪 Quality Assurance
The project includes a robust testing suite powered by `pytest`.
- **Unit Testing**: Mocks API responses and RSS feeds to ensure logic consistency without consuming API credits.
- **Integration Testing**: Validates the AI's ability to categorize complex human scenarios accurately.

## 👤 Developer
**ShadowRoot07**
Developed entirely on a mobile environment using **Termux** and **NeoVim**.

---
*Disclaimer: This tool identifies public posts for professional assessment. It does not automate direct messaging, ensuring that all final outreach remains ethical, human-led, and compliant with professional standards.*

