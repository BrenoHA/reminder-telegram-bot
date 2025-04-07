import os
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_TIME = 1

# Store reminders
reminders = {}

# Set your timezone (you can change this to your local timezone)
TIMEZONE = pytz.timezone('America/Sao_Paulo')  # Brazil timezone

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Hi! I am your reminder bot. Use /r or /reminder followed by your reminder message to set a reminder.\n'
        'Example:\n /r Buy groceries\n\n'
        'Then you will be asked to provide the time you want to be reminded.\n\n'
        'You can use the following formats: \n'
        '- HH:MM (for today)\n'
        '- HH:MM DD/MM (for a specific day this year)\n'
        '- HH:MM DD/MM/YYYY (for a specific date)\n'
        'Example: 22:55, 22:55 07/04, or 22:55 07/04/2025'
    )

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the reminder command."""
    # Get the reminder message (everything after the command)
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text('Please provide a reminder message. Example: /r Buy groceries')
        return

    # Store the message in context
    context.user_data['reminder_message'] = message
    
    current_time = datetime.now(TIMEZONE)
    await update.message.reply_text(
        f'When would you like to be reminded?')
    return WAITING_FOR_TIME

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the time input for the reminder."""
    try:
        time_input = update.message.text.strip()
        current_time = datetime.now(TIMEZONE)
        
        # Parse the time and date based on the format
        if ' ' in time_input:
            # Format with date: HH:MM DD/MM or HH:MM DD/MM/YYYY
            time_part, date_part = time_input.split(' ', 1)
            reminder_time = datetime.strptime(time_part, '%H:%M').time()
            
            # Parse the date part
            if '/' in date_part:
                date_parts = date_part.split('/')
                if len(date_parts) == 2:
                    # DD/MM format (this year)
                    day, month = map(int, date_parts)
                    year = current_time.year
                elif len(date_parts) == 3:
                    # DD/MM/YYYY format
                    day, month, year = map(int, date_parts)
                else:
                    raise ValueError("Invalid date format")
                
                # Create the target datetime
                target_datetime = datetime(year, month, day, 
                                          reminder_time.hour, 
                                          reminder_time.minute, 
                                          0, 0, TIMEZONE)
                
                # If the date is in the past, inform the user
                if target_datetime < current_time:
                    await update.message.reply_text(
                        f'The date and time you specified ({target_datetime.strftime("%d/%m/%Y %H:%M")}) is in the past. '
                        f'Please provide a future date and time.'
                    )
                    return WAITING_FOR_TIME
            else:
                raise ValueError("Invalid date format")
        else:
            # Only time format: HH:MM (for today)
            reminder_time = datetime.strptime(time_input, '%H:%M').time()
            
            # Calculate the target datetime for today
            target_datetime = current_time.replace(
                hour=reminder_time.hour,
                minute=reminder_time.minute,
                second=0,
                microsecond=0
            )
            
            # If the time has passed for today, schedule for tomorrow
            if target_datetime < current_time:
                target_datetime = target_datetime.replace(day=target_datetime.day + 1)

        # Store the reminder
        chat_id = update.effective_chat.id
        if chat_id not in reminders:
            reminders[chat_id] = []
        
        reminders[chat_id].append({
            'message': context.user_data['reminder_message'],
            'time': target_datetime
        })

        await update.message.reply_text(
            f'Reminder set at {target_datetime.strftime("%H:%M %d/%m")}:\n'
            f'{context.user_data["reminder_message"]}'
        )
        
        # Schedule the reminder
        context.job_queue.run_once(
            send_reminder,
            target_datetime,
            data={'chat_id': chat_id, 'message': context.user_data['reminder_message']}
        )

    except ValueError as e:
        await update.message.reply_text(
            'Invalid time or date format. Please use one of these formats:\n'
            '- HH:MM (for today)\n'
            '- HH:MM DD/MM (for a specific day this year)\n'
            '- HH:MM DD/MM/YYYY (for a specific date)\n'
            'Example: 22:55, 22:55 07/04, or 22:55 07/04/2025'
        )
        return WAITING_FOR_TIME

    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send the reminder message."""
    job = context.job
    await context.bot.send_message(
        job.data['chat_id'],
        f'🔔 {job.data["message"]}'
    )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('r', reminder),
            CommandHandler('reminder', reminder)
        ],
        states={
            WAITING_FOR_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)]
        },
        fallbacks=[]
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 