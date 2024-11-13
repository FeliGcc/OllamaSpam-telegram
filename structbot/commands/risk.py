import logging
import asyncio
from datetime import timedelta, datetime
from aiogram import Router, types
from aiogram.filters import Command
from function.request import generate_response
from function.chat_type import ChatTypeFilter

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)

@router.message(Command("r"))
async def risk_in_group(message: types.Message):
    modelname = "llm3.2" 
    
    if message.reply_to_message:
        prompt_text = message.reply_to_message.text
    else:
        await message.reply("Please reply to a message with the /r command.")
        return

    payload = {
        "messages": [{"role": "user", "content": prompt_text}],
        "stream": True  
    }

    full_response = "" #Variable to collect the full response from the model. Otherwise we will get the following response: How new message can and so on
    done = False #Response completion flag
    timeout = 30 #Time to answer in seconds, the longer the more complete the answer. 

    async def send_response_if_timeout():
        await asyncio.sleep(timeout)
        if not done:
            text = f"{full_response.strip()}"
            await message.reply(text)
            logging.info(f"[Response]: '{full_response.strip()}' for {message.from_user.first_name} {message.from_user.last_name}")

    try:
        send_task = asyncio.create_task(send_response_if_timeout())

        async for response in generate_response(payload, modelname):
            response_data = response.get('message', {})
            chunk = response_data.get('content', '')
            full_response += chunk

            if response_data.get("done"):
                done = True
                send_task.cancel()
                text = f"{full_response.strip()}"
                await message.reply(text)
                logging.info(f"[Response]: '{full_response.strip()}' for {message.from_user.first_name} {message.from_user.last_name}")
                break

    except Exception as e:
        await message.reply(f"Error: {str(e)}")

#The basis of checking whether it is spam or not
async def send_response(message, full_response):
    
    text = full_response.strip()
    await message.reply(text)
    logging.info(f"[Response]: '{text}' for {message.from_user.first_name} {message.from_user.last_name}")
    
    if is_spam(text):
        await handle_spam(message)
#Function determines if the response text is spam, the AI only responds with spam or not spam so check by such values
def is_spam(response_text):
    
    if "not spam" in response_text.lower():
        return False
    elif "spam" in response_text.lower():
        return True
    return False

async def handle_spam(message):
    until_date = datetime.now() + timedelta(days=30) #Set the ban for 30 days
    try:
        await message.bot.ban_chat_member(
            chat_id=message.chat.id, 
            user_id=message.reply_to_message.from_user.id, 
            until_date=until_date
        )
        await message.reply("Spam detected! User has been banned.")
        logging.info(f"Banned {message.reply_to_message.from_user.id} for spam in chat {message.chat.id}")
    except Exception as e:
        await message.reply(f"Failed to ban user: {str(e)}")
        logging.error(f"Failed to ban user {message.reply_to_message.from_user.id}: {str(e)}")
