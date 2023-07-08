###Twisted Weather Bot By Gh0st##
## You need to add 2 API keys for this bot to work. 
# #1 OpenWeather API Key https://openweathermap.org/
# #2 OpenCage API Key https://opencagedata.com/
## Both are free


##TRIGGERS FOR BOT
# !w NYC
# !weather nyc

##In order to run this bot you need to do pip3 install irc.bot and pip3 install ssl
## Then open the bot in a screen session (screen -S weatherbot) than type python3 TwistedWeatherBot.py than hold down control + a + d to minmize the screen. 
## To reopen the screen session do screen -r weatherbot


## Questions or help or just to visit come to 
### IRC.TWISTEDNET.ORG CHANNEL #DEV & #TWISTED



##gh0st 

import ssl
import irc.bot
import irc.connection
from jaraco.stream import buffer
import requests
import json
import urllib.parse
import time

irc.client.ServerConnection.buffer_class = buffer.LenientDecodingLineBuffer

class GhostBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6697, trigger='$'):
        factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname, connect_factory=factory)
        self.channels = {channel: irc.bot.Channel() for channel in channels}
        self.api_key = "OPENWEATHER API KEY"  # OpenWeatherMap API Key
        self.geocoding_api_key = "OPEN CAGE API KEY"  # OpenCage Geocoding API Key
        self.trigger = trigger

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for channel in self.channels:
            c.join(channel)

    def on_disconnect(self, c, e):
        c.reconnect()

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        message = e.arguments[0].strip()
        if message.startswith(self.trigger):
            command = message[len(self.trigger):].split(' ', 1)
            if len(command) > 0:
                trigger = command[0]
                if trigger in ['weather', 'w']:
                    location = command[1].strip() if len(command) > 1 else ''
                    if location:
                        full_location = self.get_city_name(location)
                        if not full_location:
                            c.privmsg(e.target, "Unable to get location information.")
                        else:
                            weather_info = self.get_weather(full_location)
                            c.privmsg(e.target, weather_info)

    def get_city_name(self, location):
        base_url = 'https://api.opencagedata.com/geocode/v1/json?'

        params = urllib.parse.urlencode({
            'q': location,
            'key': self.geocoding_api_key,
            'no_annotations': 1
        })

        response = requests.get(base_url + params)

        if response.status_code != 200:
            return None

        data = response.json()
        components = data['results'][0]['components']
        city = components.get('city') or components.get('town') or components.get('village')
        country = components.get('country_code')

        return f"{city},{country}" if city and country else None

    def get_weather(self, full_location):
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": full_location, "appid": self.api_key}
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            description = data["weather"][0]["description"]
            temp_k = data["main"]["temp"]
            temp_c = round(temp_k - 273.15, 2)
            temp_f = round((temp_k - 273.15) * 9 / 5 + 32, 2)
            temp_max_k = data["main"]["temp_max"]
            temp_min_k = data["main"]["temp_min"]
            temp_max_c = round(temp_max_k - 273.15, 2)
            temp_min_c = round(temp_min_k - 273.15, 2)
            temp_max_f = round((temp_max_k - 273.15) * 9 / 5 + 32, 2)
            temp_min_f = round((temp_min_k - 273.15) * 9 / 5 + 32, 2)

            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            pressure = data['main']['pressure']
            sunrise = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(data['sys']['sunrise']))
            sunset = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(data['sys']['sunset']))

            weather_emoji = {
                'clear sky': '☀️',
                'few clouds': '⛅',
                'scattered clouds': '☁️',
                'broken clouds': '☁️',
                'shower rain': '🌧️',
                'rain': '🌧️',
                'thunderstorm': '⛈️',
                'snow': '❄️',
                'mist': '🌫️'
            }

            temp_emoji = '🥶' if temp_c < 0 else '❄️' if temp_c < 10 else '⛄' if temp_c < 20 else '🌼' if temp_c < 30 else '🔥'
            emoji = weather_emoji.get(description, '')

            weather_info = f"Weather in {full_location}: {description} {emoji}, Current: {temp_f}°F / {temp_c}°C {temp_emoji}, High: {temp_max_f}°F / {temp_max_c}°C, Low: {temp_min_f}°F / {temp_min_c}°C, Humidity: {humidity}%, Wind Speed: {wind_speed} m/s, Pressure: {pressure} hPa, Sunrise: {sunrise}, Sunset: {sunset}"
            return weather_info
        else:
            return "Unable to get weather information."


def main():
    server = "irc.twistednet.org"
    channels = ["#dev", "#twisted", "#0fucks", "#chat", "#heh"]
    nickname = "Weathertest"
    trigger = '!'

    bot = GhostBot(channels, nickname, server, trigger=trigger)
    bot.start()

if __name__ == "__main__":
    main()

