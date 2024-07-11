# Twisted Weather Bot By Gh0st

## Requirements
To run this bot, you need to obtain two API keys:
1. **OpenWeather API Key**: [OpenWeather API Key](https://openweathermap.org/)
2. **OpenCage API Key**: [OpenCage API Key](https://opencagedata.com/)

Both of these API keys are free.

## Installation

1. **Install Required Libraries**

   You need to install the required libraries for the bot. Run the following commands:

   ```bash
   pip3 install irc.bot
   pip3 install ssl
   pip3 install requests
   pip3 install jaraco.stream

Save the Script

Save the bot script to a file named TwistedWeatherBot.py.

Edit the Script

Edit the script to add your API keys:


weather_api_key = "your_openweather_api_key"
geocoding_api_key = "your_opencage_api_key"

Running the Bot
To keep the bot running even when you close the console, it is recommended to use screen.

Start a Screen Session

Open a screen session named weatherbot:


screen -S weatherbot
Run the Bot

Within the screen session, run the bot:


python3 TwistedWeatherBot.py
Detach the Screen Session

Detach from the screen session to keep the bot running in the background:


Ctrl + A + D
Reattach to the Screen Session

To reattach to the screen session:
screen -r weatherbot

Bot Commands

Triggers for the Bot
!w <location>: Get the current weather for the specified location.
Example: !w NYC
!weather <location>: Alias for !w <location>.
Example: !weather NYC
Commands
!w <location>: Get the current weather for the specified location.
Example: !w NYC
!w: Get the current weather for your saved location.
!check <nick>: Check the weather for the saved location of the specified nickname.
Example: !check username
!setweather <zip or location>: Set your weather location using a zip code or location name.
Example: !setweather 10001
!join <#channel>: Make the bot join the specified channel.
Example: !join #weather
!part <#channel>: Make the bot leave the specified channel.
Example: !part #weather
!help: Show the help message.
Questions or Help
For questions, help, or to visit, join us at:

IRC.TWISTEDNET.ORG CHANNEL #DEV & #TWISTED

