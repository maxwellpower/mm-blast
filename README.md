# Mattermost Direct Message Blaster

Send direct messages to a list of user IDs in Mattermost as a bot. This tool can be run as a standalone script or as an API server that listens for slash commands from Mattermost.

## Prerequisites

- Python 3.9+
- Docker (optional, but recommended for deployment)
- A Mattermost server with administrative access (for setting up the slash command)

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/maxwellpower/mm-blast.git
   cd mm-blast
   ```

2. Install the required Python packages:

   ```bash
   pip install fastapi uvicorn requests termcolor
   ```

3. Set up the necessary environment variables. You can either export them directly or use an `.env` file. The required variables are:

   - `MATTERMOST_URL`: The URL of your Mattermost server.
   - `BOT_API_KEY`: The API key for your bot.
   - `USER_IDS_OR_CSV_PATH`: Either a comma-separated list of user IDs or a path to a CSV file containing user IDs.
   - `MESSAGE` or `MESSAGE_FILE_PATH`: The message to send. Can be provided directly as a string or as a path to a file containing the message.
   - `RUN_MODE`: Either "script" (default) for standalone mode or "api" for API server mode.
   - `SHARED_SECRET`: A secret key used to authenticate incoming API requests (only required for API mode).

## Usage

### Standalone Script Mode

In this mode, the script will send messages to users based on the provided user IDs and message.

```bash
python main.py
```

### API Server Mode with Mattermost Slash Command

1. Start the API server:

   ```bash
   export RUN_MODE=api
   python main.py
   ```

2. In Mattermost, go to **Main Menu > Integrations > Slash Commands**.
3. Click **Add Slash Command**.
4. Fill in the details:
   - **Title**: DM Blaster
   - **Description**: Send direct messages to a list of users.
   - **Command Trigger Word**: `blast` (or any other trigger word you prefer)
   - **Request URL**: `http://<YOUR_SERVER_IP>:8000/send_message`
   - **Request Method**: `POST`
   - **Response Username**: (Optional) The bot's username.
   - **Autocomplete**: Enable this and provide a hint like `send` to guide users.
5. Click **Save**.

Now, in any Mattermost channel, you can use the slash command `/blast send` to trigger the message sending.

### Using the Slash Command in Mattermost

Once you've set up the slash command in Mattermost (as described in the previous section), you can use it to send direct messages to multiple users. Here's how:

1. **Syntax**:
   ```
   /blast send --users=<USER_IDS> --message=<MESSAGE>
   ```

   - `<USER_IDS>`: A comma-separated list of user IDs or hashes to whom you want to send the message.
   - `<MESSAGE>`: The message you want to send. You can format it using Mattermost's markdown syntax for richer content.

2. **Example**:
   ```
   /blast send --users=user1ID,user2ID,user3ID --message=Hello! This is a *test* message.
   ```

   This will send the message "Hello! This is a *test* message." to the users with IDs `user1ID`, `user2ID`, and `user3ID`.

3. **Notes**:
    - Ensure that you've set permissions in Mattermost to restrict the usage of the slash command to trusted roles.
    - The slash command will provide feedback in the channel or as a direct message to the admin, indicating the success or failure of the message sending process.

## Docker Deployment

### Run the Docker container:

   ```bash
   docker run --env-file .env ghcr.io/maxwellpower/mm-blast
   ```

### Running the Docker Container with Mounted Volumes

1. Add your files to a local folder like "resources" and expose that folder to the app directory in the container.

   ```bash
   docker run --env-file .env -v resources:/app ghcr.io/maxwellpower/mm-blast
   ```

   Note: If you're running in API mode, make sure to expose port 8000:

   ```bash
   docker run --env-file .env -p 8000:8000 ghcr.io/maxwellpower/mm-blast
   ```
