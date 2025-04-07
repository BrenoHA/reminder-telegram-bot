# Telegram Reminder Bot

A simple Telegram bot that helps you set reminders. When you send a message with `/r` or `/reminder` followed by your reminder text, the bot will ask you when you want to be reminded and send you a message at the specified time.

## Setup

1. Create a new bot and get your token from [@BotFather](https://t.me/botfather) on Telegram
2. Clone this repository
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the `.env` file and add your bot token:
   ```bash
   cp .env .env.local
   ```
5. Edit `.env.local` and replace `your_telegram_bot_token_here` with your actual bot token

## Usage

1. Start the bot:

   ```bash
   python reminder_bot.py
   ```

2. In Telegram, start a chat with your bot and send `/start` to begin

3. To set a reminder, use either:

   - `/r Your reminder message`
   - `/reminder Your reminder message`

4. The bot will ask you for the time in 24-hour format (HH:MM)

5. Enter the time (e.g., `14:30` for 2:30 PM)

The bot will confirm your reminder and send you a message at the specified time.

## Features

- Simple reminder setting with `/r` or `/reminder` commands
- 24-hour time format support
- Automatic scheduling for next day if time has passed
- Persistent reminders across bot restarts
