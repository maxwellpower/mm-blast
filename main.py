#! /usr/local/bin/python

# Mattermost Direct Message Blaster

# Copyright (c) 2023 Maxwell Power
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

VERSION = "1.0.2"

import os
import requests
import csv
from termcolor import colored
from fastapi import FastAPI, HTTPException, Request, Depends
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)
logger = logging.getLogger(f"MM-BLAST v{VERSION}")

app = FastAPI()

SHARED_SECRET = os.environ.get("SHARED_SECRET")

def verify_shared_secret(request: Request):
    secret = request.headers.get("X-Shared-Secret")
    if not secret or secret != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return True

@app.post("/send_message")
async def api_send_message(request: Request, _=Depends(verify_shared_secret)):
    data = await request.json()
    command_text = data.get("text", "")

    if command_text == "send":
        try:
            send_messages_to_users()
            logger.info("Messages sent successfully via API.")
            return {"response_type": "in_channel", "text": "Messages sent successfully!"}
        except Exception as e:
            logger.error(f"Error while sending messages via API: {str(e)}")
            return {"response_type": "ephemeral", "text": f"Error: {str(e)}"}
    else:
        logger.warning(f"Unknown command received via API: {command_text}")
        return {"response_type": "ephemeral", "text": "Unknown command."}

def send_messages_to_users():

    def read_user_ids_from_csv(file_path):
        with open(file_path, 'r') as file:
            return [row[0] for row in csv.reader(file)]

    # Get environment variables or prompt user for input
    MATTERMOST_URL = os.environ.get("MATTERMOST_URL", None)
    if not MATTERMOST_URL:
        MATTERMOST_URL = input("Enter your Mattermost server URL: ")

    user_ids_input = os.environ.get("USER_IDS_OR_CSV_PATH", None)
    if not user_ids_input:
        user_ids_input = input("Enter the list of user ID hashes (comma-separated) or path to CSV file: ")

    # Check if input is a file path or comma-separated list
    if os.path.isfile(user_ids_input):
        user_ids = read_user_ids_from_csv(user_ids_input)
    else:
        user_ids = user_ids_input.split(",")

    message = os.environ.get("MESSAGE", None)
    if not message:
        message_file_path = os.environ.get("MESSAGE_FILE_PATH", None)
        if not message_file_path:
            message_file_path = input("Enter the path to the message file: ")

        with open(message_file_path, 'r') as file:
            message = file.read()

    if not message:
        logger.error("No message provided in either the environment variable or the file.")
        exit(1)

    bot_api_key = os.environ.get("BOT_API_KEY", None)
    if not bot_api_key:
        bot_api_key = input("Enter the bot API key: ")

    headers = {
        "Authorization": f"Bearer {bot_api_key}",
        "Content-Type": "application/json"
    }

    VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() == "true"
    if not VERIFY_SSL:
        logger.warning("VERIFY SSL DISABLED. SSL WARNINGS WILL BE PRINTED FOR ALL API CALLS.")

    # Get the bot's user ID
    GET_ME_ENDPOINT = "/api/v4/users/me"
    response = requests.get(MATTERMOST_URL + GET_ME_ENDPOINT, headers=headers, verify=VERIFY_SSL)
    
    if response.status_code != 200:
        logger.error(f"Failed to get the bot's user ID. Status Code: {response.status_code}. Response: {response.text}")
        exit(1)
    
    BOT_USER_ID = response.json()["id"]

    CREATE_DM_ENDPOINT = "/api/v4/channels/direct"
    CREATE_POST_ENDPOINT = "/api/v4/posts"

    # Send DM to each user
    for user_id in user_ids:
        # Create or get DM channel ID
        response = requests.post(MATTERMOST_URL + CREATE_DM_ENDPOINT, headers=headers, verify=VERIFY_SSL, json=[BOT_USER_ID, user_id])
        if response.status_code != 201:
            logger.warning(f"Failed to get or create DM channel for user {user_id}. Error: {response.text}")
            continue
        channel_id = response.json()["id"]

        # Post the message
        payload = {
            "channel_id": channel_id,
            "message": message
        }
        response = requests.post(MATTERMOST_URL + CREATE_POST_ENDPOINT, headers=headers, verify=VERIFY_SSL, json=payload)
        if response.status_code != 201:
            logger.warning(f"Failed to send message to user {user_id}. Error: {response.text}")
        else:
            logger.info(f"Sent message to user {user_id}.")
    logger.info("Process Complete!")

if __name__ == "__main__":
    required_env_vars = ["MATTERMOST_URL", "BOT_API_KEY"]
    for var in required_env_vars:
        if not os.environ.get(var):
            logger.error(f"Environment variable {var} not set. Exiting.")
            exit(1)

    mode = os.environ.get("RUN_MODE", "script")
    if mode == "api":
        import uvicorn
        logger.info("Starting API server.")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        send_messages_to_users()
