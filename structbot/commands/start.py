import asyncio
from aiogram import Router, types
from aiogram.filters import CommandStart
from function.chat_type import ChatTypeFilter

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)

@router.message(CommandStart()) 
async def start_in_group(message: types.Message):
    await message.reply("Hi! I'm a bot with the Ollama API realization👾\nMy target is to recognize whether a particular message is spam or not itself")