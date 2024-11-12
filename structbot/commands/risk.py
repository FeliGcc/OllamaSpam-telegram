import logging
import asyncio
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