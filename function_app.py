from openai import OpenAI
from receiptProcess import *
from databaseUpdate import *
from dotenv import load_dotenv
import os
from telegram import Update, Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import azure.functions as func
import logging
import json
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv(dotenv_path=r'keys.env')
openai_api_key = os.getenv('OPENAI_API_KEY')

TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_BLOB_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)


DOCUMENT_AI_ENDPOINT = os.getenv('DOCUMENT_AI_ENDPOINT')
DOCUMENT_AI_KEY = os.getenv('DOCUMENT_AI_KEY')
#formUrl = os.getenv('formUrl')

# Initialize conversation states
CHOOSING_LANGUAGE,UPLOAD_RECEIPT= range(2)


async def set_language(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    selected_lang = query.data.split('_')[-1]  # Extract the language code (e.g., 'en', 'fr', 'ar')

    # Save the language choice
    context.user_data["language"] = selected_lang

    # Confirm the choice and proceed
    await query.edit_message_text(f"Language set to {selected_lang.upper()}. Please restart the chat by sending /start.")
    return await start(update, context)  # Restart the conversation in the selected language

def get_language(update: Update):
    # Detect user's language based on the user's profile or request
    return update.message.from_user.language_code if update.message else 'en'

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Upload photo')
    return UPLOAD_RECEIPT

async def upload_receipt(update: Update, context: CallbackContext):
    # Check if the user uploaded a photo
   user_id = update.message.from_user.id
   if update.message.photo:
    photo_id = update.message.photo[-1].file_id  # Largest resolution
    context.user_data['photo_id'] = photo_id

    bot = Bot(token=TOKEN)
    try:
        file = await bot.get_file(photo_id)
        file_stream = BytesIO()
        await file.download_to_memory(file_stream)
        file_stream.seek(0)  # Reset the stream position

            # Upload the stream directly to Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(
                container=AZURE_BLOB_CONTAINER_NAME, blob=f"receipts/{photo_id}.jpg"
            )

        blob_client.upload_blob(file_stream, overwrite=True)
        blob_url = blob_client.url
        
    except Exception as e:
        await update.message.reply_text(f"Error uploading file to Blob Storage: {str(e)}")
    try:
        transactionUpload(analyze_layout(DOCUMENT_AI_ENDPOINT, DOCUMENT_AI_KEY,blob_url),str(user_id))
        await update.message.reply_text("Upload Successful. Your transaction history has been updated. What would you like to do next?")
        
    except Exception as e:
        if 'Violation of PRIMARY KEY' in str(e):
            await update.message.reply_text(f"Receipt has already been uploaded for today.")
            await update.message.reply_text(f"Your transaction history is: "+ str(monthlyAnalysis(str(user_id))))
            
        else:
            await update.message.reply_text(f"Analysis error: {str(e)}")
        # Get the blob URL
    

            # Call your function to process the receipt

   else:
    await update.message.reply_text('Invalid Photo. Please upload a valid receipt.') # Retry photo upload


# Create the conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],  # Standard entry point
    states={
        UPLOAD_RECEIPT: [MessageHandler(filters.PHOTO, upload_receipt)]  # Handle photo upload here
    },
    fallbacks=[CommandHandler('start', start)]  # Fallback if user issues any invalid command
)  
async def run_bot():
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(conv_handler)
    #application.add_handler(CallbackQueryHandler(item_selection, pattern="^select_"))


    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    #await application.idle()


# Azure Functions handler
app = func.FunctionApp()
@app.route(route="http_trigger_better_buy")
async def main(req) -> str:
    """Entry point for Azure Functions."""
    import asyncio

    # Run the bot asynchronously
    asyncio.create_task(run_bot())
    return "Bot is running"


if __name__ == "__main__":
    import asyncio

    # Local testing
    asyncio.run(run_bot())
