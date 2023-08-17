# Roundabarter

Roundabarter is a Telegram bot that notifies you when a new Carousell listing has been added.


## Installation

Roundabarter has been dockerized and thus it is recommended that you use Docker for deployment.

1. Install [Docker Desktop](https://docs.docker.com/get-docker/)

2. Build the Docker image for the server using:

    ```
    $ docker build -t roundabarter-server server/.
    ```

3. Build the Docker image for the client using:

    ```
    $ docker build -t roundabarter-telegram-bot client/.
    ```

4. [Create a new Telegram bot and obtain your bot token](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

5. [Obtain your Telegram user ID](https://www.itgeared.com/how-to-find-someones-telegram-id/#How%20To%20Find%20Someone's%20Telegram%20Id:~:text=you%20find%20it.-,How%20To%20Find%20Someone%E2%80%99s%20Telegram%20ID,-Your%20Telegram%20ID)

6. In `docker-compose.yml`, replace `<YOUR TELEGRAM BOT TOKEN>` and `<YOUR TELEGRAM USER ID>` with your bot token and Telegram user ID respectively

    Your `docker-compose.yml` file should look similar to this:

    ```yml
    services:
      server:
        image: roundabarter-server
        container_name: roundabarter-server
        volumes:
          - roundabarter-db:/etc/roundabarter
        environment:
          DATABASE_LOCATION: /etc/roundabarter/database.db
      telegram-bot:
        image: roundabarter-telegram-bot
        container_name: roundabarter-telegram-bot
        environment:
          TELEGRAM_BOT_API_TOKEN: 4839574812:AAFD39kkdpWt3ywyRZergyOLMaJhac60qc
          FLASK_API_URL: http://roundabarter-server:5000
          DEFAULT_SCRAPE_INTERVAL: 600
          LIST_OF_ADMINS: "[123456789]"

    volumes:
      roundabarter-db:
    ```

7. Start the application using:
    ```
    $ docker compose up
    ```

## Usage - Bot Commands

### `/start`

Initialises the bot - use this command each time the bot is restarted

### `/new <name of tracked search> <Carousell search URL>`

Sets up a new tracked search with the given name and Carousell search URL

Ensure that Carousell search is sorted by 'Recent' listings before copying the URL

### `/list`
  
Displays a list of all tracked searches

### `/fetch <name of tracked search>`

Retrieves the latest listings of a tracked search

### `/update <name of tracked search> <new scrape interval in seconds>`

Updates the scrape interval of a tracked search

### `/remove <name of tracked search`

Removes a tracked search