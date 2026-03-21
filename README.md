📊 Pixela Habit Tracker Bot
A Stateless Telegram Bot for Cloud-Synced Habit Tracking

This project is a Telegram bot designed to help users track daily habits using the Pixela API. Unlike traditional bots that rely heavily on local databases, this bot uses a Stateless Architecture, fetching habit definitions (names, units, and colors) directly from the cloud upon login.

🛠 Features
User Management: Register a new Pixela account or log into an existing one directly via Telegram.

Cloud-Sync (Stateless): Habit names and units are pulled dynamically from Pixela, ensuring your data is accessible from any device.

Interactive Logging: Uses Telegram’s InlineKeyboardMarkup for a seamless one-tap logging experience.

Data Visualization: Automatically generates links to your personal Pixela heatmaps to track progress over time.

Session Persistence: Integrated with PicklePersistence to keep you logged in even if the bot server restarts.

🏗️ Technical Architecture
The bot is split into two main modules to ensure clean, maintainable code:

app.py: The API Wrapper. Handles all HTTP requests to Pixela, including user creation, graph generation, and pixel updates.

bot.py: The Interface. Handles the Telegram State Machine (ConversationHandler), command routing, and user session management.

🚀 Tech Stack
Language: Python 3.10+

Framework: python-telegram-bot (v20+)

API: Pixela

Deployment: Render (Background Worker)

Environment Management: python-dotenv

📖 Setup & Installation
1. Prerequisites

A Telegram Bot Token from @BotFather.

Python 3.10 or higher installed.

2. Installation

Bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/HabitTracker.git
cd HabitTracker

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

3. Environment Variables

Create a .env file in the root directory and add your token:

Plaintext
TELEGRAM_BOT_TOKEN=your_secret_bot_token_here

4. Running the Bot
   
Bash
python bot.py


🎮 Bot Commands

/register	Create a new Pixela account with a username and token.

/login	Log in and sync your existing habits from the cloud.

/custom	Step-by-step setup for your 2 primary habits.

/done	Log activity for today.

/view	Get links to your habit heatmaps.

/logout	Wipe local session data.
