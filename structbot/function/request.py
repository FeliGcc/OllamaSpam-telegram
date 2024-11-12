import aiohttp
import json
import logging
from aiohttp import ClientTimeout
from config.conf import API_Ollama, Port

timeout = 3000 #The request will terminate after 3 seconds if no response is received from the server

#The Ollama API request function was borrowed from https://github.com/ruecat/ollama-telegram/blob/main/bot/func/interactions.py#L102
async def generate_response(payload: dict, modelname: str):
    client_timeout = ClientTimeout(total=int(timeout))
    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        url = f"http://{API_Ollama}:{Port}/api/chat" #Form a link for Ollama operation, these links are located in the config folder, conf.py
        ollama_payload = { #Request - https://github.com/ollama/ollama/blob/main/docs/api.md#request-10
            "model": modelname,
            "messages": payload.get("messages", []),
            "stream": payload.get("stream", True)
        }
        async for response in send_request(session, url, ollama_payload): 
            yield response

async def send_request(session, url, payload): #Function for sending a request to an API and processing the data stream in the response
    logging.info(f"Sending request to Ollama API: {url}")
    logging.info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with session.post(url, json=payload) as response: #Post query using json
            if response.status != 200:
                error_text = await response.text()
                logging.error(f"API Error: {response.status} - {error_text}")
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"API Error: {error_text}"
                )

            buffer = b"" #Buffer for data accumulation
            async for chunk in response.content.iter_any(): #Read the answer in parts
                buffer += chunk #Add the read fragment to the buffer
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if line:
                        yield await process_line(line)

    except aiohttp.ClientError as e:
        logging.error(f"Client Error during request: {e}")
        raise

#Function to convert a response to JSON
async def process_line(line):
    try:
        logging.info(f"Received line: {line}")
        return json.loads(line)
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        logging.error(f"Problematic line: {line}")
        return None