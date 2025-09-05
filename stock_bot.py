import os
import logging
from datetime import datetime, timedelta
import io
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load API keys from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Welcome to the Stock Analysis Bot!\n\n"
        "Send me any stock symbol:\n"
        "• For Indian stocks: Add '.NS' for NSE or '.BO' for BSE\n"
        "  Examples: 'RELIANCE.NS', 'TCS.NS', 'INFY.BO'\n"
        "• For US stocks: Just the symbol\n"
        "  Examples: 'AAPL', 'MSFT'\n\n"
        "Try sending 'RELIANCE.NS' for Reliance Industries NSE stock analysis!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 Stock Analysis Bot Help:\n\n"
        "For Indian Stocks (NSE/BSE):\n"
        "• Add '.NS' for NSE stocks: RELIANCE.NS, TCS.NS\n"
        "• Add '.BO' for BSE stocks: INFY.BO, SBIN.BO\n\n"
        "For US Stocks:\n"
        "• Just type the symbol: AAPL, MSFT\n\n"
        "Popular Indian Stocks:\n"
        "• RELIANCE.NS - Reliance Industries\n"
        "• TCS.NS - Tata Consultancy Services\n"
        "• HDFCBANK.NS - HDFC Bank\n"
        "• INFY.NS - Infosys\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

def get_stock_data(symbol: str):
    """Fetch stock data using yfinance."""
    try:
        # Handle Indian stock symbols
        original_symbol = symbol
        if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            # If no exchange suffix is provided, try NSE by default for common Indian symbols
            if symbol in ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'TATAMOTORS', 'WIPRO']:
                symbol = f"{symbol}.NS"
        
        logger.info(f"Fetching data for symbol: {symbol}")
        stock = yf.Ticker(symbol)
        
        # Try to access info to verify the connection
        logger.info("Fetching stock info...")
        info = stock.info
        if not info or 'regularMarketPrice' not in info:
            logger.error("No info returned from yfinance")
            
            # Provide a more helpful error message for Indian stocks
            if original_symbol == symbol:
                return {
                    'success': False,
                    'error': f'No data available for {symbol}. If this is an Indian stock, try adding .NS (for NSE) or .BO (for BSE) to the symbol.'
                }
            else:
                return {'success': False, 'error': f'No data available for this symbol. Please check if the symbol is correct.'}
            
        logger.info("Successfully got stock info")
        
        # Get historical data for the past 30 days
        logger.info("Fetching historical data...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        history = stock.history(start=start_date, end=end_date)
        
        if history.empty:
            logger.error("No historical data available")
            return {'success': False, 'error': 'No historical data available'}
            
        logger.info("Successfully got historical data")
        
        return {
            'info': info,
            'history': history,
            'success': True
        }
    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        return {'success': False, 'error': str(e)}

def generate_chart(history):
    """Generate a stock price chart using matplotlib."""
    try:
        # Set the backend to Agg explicitly
        import matplotlib
        matplotlib.use('Agg')
        
        # Clear any existing plots
        plt.clf()
        
        # Create new figure
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Plot the data
        ax.plot(history.index, history['Close'], 'b-', linewidth=2)
        
        # Customize the plot
        ax.set_title('30-Day Stock Price History', pad=20)
        ax.set_xlabel('Date')
        ax.set_ylabel('Price (USD)')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Format dates on x-axis
        plt.xticks(rotation=45)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Clean up
        plt.close(fig)
        
        return buf
    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        raise Exception(f"Failed to generate chart: {str(e)}")

def get_perplexity_analysis(stock_data):
    """Get stock analysis from Perplexity API."""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Analyze the following stock data and provide a very concise 3-4 sentence summary:
    Current Price: ${stock_data['info'].get('currentPrice', 'N/A')}
    Market Cap: ${stock_data['info'].get('marketCap', 'N/A'):,}
    P/E Ratio: {stock_data['info'].get('trailingPE', 'N/A')}
    52-Week High: ${stock_data['info'].get('fiftyTwoWeekHigh', 'N/A')}
    52-Week Low: ${stock_data['info'].get('fiftyTwoWeekLow', 'N/A')}
    Volume: {stock_data['info'].get('volume', 'N/A'):,}
    
    Focus on: 1) Current position vs 52-week range, 2) Key valuation insight from P/E ratio, 3) Brief outlook. Use plain text without markdown formatting."""
    
    try:
        payload = {
            "model": "sonar-pro",  # Updated to use sonar-pro model
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial analyst providing concise stock analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Log the response for debugging
        logger.info(f"Perplexity API Response Status: {response.status_code}")
        logger.info(f"Perplexity API Response Headers: {response.headers}")
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Perplexity API Error: {error_text}")
            return f"Unable to generate analysis. Error: {error_text}"
            
        response_json = response.json()
        logger.info(f"Perplexity API Response: {response_json}")
        
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            logger.error(f"Unexpected API response format: {response_json}")
            return "Unable to generate analysis: Unexpected API response format"
            
    except requests.exceptions.Timeout:
        logger.error("Perplexity API request timed out")
        return "Unable to generate analysis: Request timed out"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return f"Unable to generate analysis: Network error - {str(e)}"
    except Exception as e:
        logger.error(f"Error getting Perplexity analysis: {e}")
        return f"Unable to generate analysis: {str(e)}"

def format_stock_message(symbol: str, stock_data: dict, analysis: str):
    """Format the stock analysis message."""
    info = stock_data['info']
    
    # Format market cap to be more readable
    market_cap = info.get('marketCap', 'N/A')
    if isinstance(market_cap, (int, float)):
        if market_cap >= 1_000_000_000_000:  # Trillion
            market_cap = f"${market_cap / 1_000_000_000_000:.2f}T"
        elif market_cap >= 1_000_000_000:  # Billion
            market_cap = f"${market_cap / 1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:  # Million
            market_cap = f"${market_cap / 1_000_000:.2f}M"
    
    # Format numbers
    current_price = info.get('currentPrice', 'N/A')
    current_price = f"${current_price:.2f}" if isinstance(current_price, (int, float)) else 'N/A'
    
    prev_close = info.get('previousClose', 'N/A')
    prev_close = f"${prev_close:.2f}" if isinstance(prev_close, (int, float)) else 'N/A'
    
    pe_ratio = info.get('trailingPE', 'N/A')
    pe_ratio = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else 'N/A'
    
    # Clean up the analysis text - remove markdown formatting
    clean_analysis = analysis
    clean_analysis = clean_analysis.replace('**', '')  # Remove bold
    clean_analysis = clean_analysis.replace('*', '')   # Remove any remaining asterisks
    clean_analysis = clean_analysis.replace('`', '')   # Remove code blocks
    clean_analysis = clean_analysis.replace('_', '')   # Remove underscores
    clean_analysis = clean_analysis.replace('#', '')   # Remove headers
    
    # Format the message with minimal markdown
    message = (
        f"📊 *{symbol.upper()} Stock Analysis*\n\n"
        f"💰 Current Price: {current_price}\n"
        f"📈 Previous Close: {prev_close}\n"
        f"💹 Market Cap: {market_cap}\n"
        f"📊 P/E Ratio: {pe_ratio}\n\n"
        f"📝 *Analysis*:\n"
        f"{clean_analysis}\n\n"
    )
    
    # Ensure the message length fits Telegram's limits
    if len(message) > 1000:  # Telegram's limit is 1024 for caption
        message = message[:997] + "..."
    
    return message

async def handle_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stock symbol messages."""
    symbol = update.message.text.strip().upper()
    
    # Send initial processing message
    processing_message = await update.message.reply_text(
        f"🔄 Processing {symbol}... Please wait."
    )
    
    try:
        logger.info(f"Processing request for symbol: {symbol}")
        
        # Fetch stock data
        stock_data = get_stock_data(symbol)
        
        if not stock_data['success']:
            error_msg = stock_data.get('error', 'Unknown error')
            logger.error(f"Failed to get stock data: {error_msg}")
            await processing_message.edit_text(
                f"❌ Error: Unable to fetch data for {symbol}. Error: {error_msg}"
            )
            return
        
        logger.info("Successfully fetched stock data, generating chart...")
        
        try:
            # Generate chart
            chart_buf = generate_chart(stock_data['history'])
            logger.info("Chart generated successfully")
            
            # Get analysis from Perplexity
            logger.info("Requesting analysis from Perplexity API...")
            analysis = get_perplexity_analysis(stock_data)
            logger.info("Analysis received")
            
            # Format message
            message = format_stock_message(symbol, stock_data, analysis)
            
            # Send chart with caption
            logger.info("Sending response to user...")
            await update.message.reply_photo(
                photo=chart_buf,
                caption=message,
                parse_mode='Markdown'
            )
            logger.info("Response sent successfully")
            
            # Delete processing message
            await processing_message.delete()
            
        except Exception as chart_error:
            logger.error(f"Error in chart generation or sending: {str(chart_error)}")
            # If we fail after getting stock data, try to send at least the text analysis
            error_message = f"""📊 *{symbol.upper()} - Stock Analysis*\n\n"""
            error_message += f"❌ Chart generation failed, but here's the analysis:\n\n"
            error_message += format_stock_message(symbol, stock_data, analysis)
            await processing_message.edit_text(error_message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error processing stock request: {str(e)}")
        await processing_message.edit_text(
            f"❌ Error processing {symbol}: {str(e)}\nPlease try again later."
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
