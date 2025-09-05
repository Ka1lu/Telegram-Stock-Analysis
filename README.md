# 📊 Stock Analysis Telegram Bot  

A **Telegram bot** that fetches real-time stock market data, generates price trend charts, and provides **AI-powered financial analysis**.  
Built using **Python, yFinance, Matplotlib, Telegram API, and Perplexity AI**.  

---

## 🚀 Features  
- ✅ Fetch **real-time stock data** (Indian & US markets) via yFinance  
- 📈 Generate **30-day price history charts** using Matplotlib  
- 🤖 Get **concise stock insights** powered by Perplexity AI  
- 💬 Simple **Telegram Bot interface** with `/start` and `/help` commands  

---

## 🛠 Tech Stack  
- Python  
- yFinance – Stock data  
- Matplotlib – Charting  
- Telegram Bot API – Interaction  
- Perplexity AI API – Stock analysis  
- dotenv & logging – Config & monitoring  

---

## ⚡ Setup Instructions  

1. Clone the repository  
   git clone https://github.com/Ka1lu/Telegram-Stock-Analysis.git  
   cd Telegram-Stock-Analysis  

2. Create a virtual environment (optional but recommended)  
   python -m venv venv  
   source venv/bin/activate   # On macOS/Linux  
   venv\Scripts\activate      # On Windows  

3. Install dependencies  
   pip install -r requirements.txt  

4. Add environment variables  
   Create a `.env` file in the root directory with the following:  
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token  
   PERPLEXITY_API_KEY=your_perplexity_api_key  

5. Run the bot  
   python bot.py  

---

## 📌 Usage  

1. Start the bot on Telegram with `/start`  
2. Send stock symbols:  
   - Indian Stocks (NSE/BSE): Add suffix `.NS` or `.BO`  
     - Example: RELIANCE.NS, INFY.BO  
   - US Stocks: Just the symbol  
     - Example: AAPL, MSFT  
3. Get:  
   - Current price & market data  
   - 30-day stock price chart  
   - AI-powered summary  

---

## 🖼 Example  

- Input: AAPL  
- Output:  
  - Stock chart (30-day history)  
  - Metrics: Current Price, Market Cap, P/E Ratio, etc.  
  - Concise analysis from Perplexity AI  

---

## 📬 Contact  
If you'd like to know more about this project, feel free to connect with me on [LinkedIn](https://linkedin.com/in/kailas-binukumar) or raise an issue here on GitHub.  
