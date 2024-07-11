import ssl
import irc.bot
import irc.connection
import time
import requests
import random
import datetime
import json
from jaraco.stream import buffer
import threading

class GhostBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6697, weather_api_key='', geocoding_api_key=''):
        irc.client.ServerConnection.buffer_class = buffer.LenientDecodingLineBuffer
        factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        super().__init__([(server, port)], nickname, nickname, connect_factory=factory)
        self.channels_to_join = channels
        self.weather_api_key = weather_api_key
        self.geocoding_api_key = geocoding_api_key
        self.user_locations = self.load_data('user_locations.json', dict)
        self.dynamic_channels = self.load_data('dynamic_channels.json', list)
        self.alert_cooldown = {}
        self.is_ready = False
        self.joined_channels = set()
        self.location_queue = []
        self.check_interval = 3600
        self.alert_cooldown_period = 24 * 3600

    def on_all_raw_messages(self, c, e):
        print("[RAW MESSAGE]:", e.arguments[0])

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for channel in self.channels_to_join + self.dynamic_channels:
            c.join(channel)

    def on_join(self, c, e):
        joined_channel = e.target
        if joined_channel in self.channels_to_join + self.dynamic_channels:
            self.joined_channels.add(joined_channel)
            if self.joined_channels == set(self.channels_to_join + self.dynamic_channels):
                self.is_ready = True
                self.schedule_weather_alerts()

    def get_coordinates(self, location):
        geocode_url = f"https://geocode.maps.co/search?q={location}&api_key={self.geocoding_api_key}"
        try:
            response = requests.get(geocode_url)
            response.raise_for_status()
            data = response.json()
            if data:
                lat = data[0].get('lat')
                lon = data[0].get('lon')
                display_name = data[0].get('display_name', location)
                return lat, lon, display_name
        except requests.RequestException as e:
            print(f"Error fetching coordinates: {e}")
        return None, None, location

    def schedule_weather_alerts(self):
        if self.is_ready:
            if not self.location_queue:
                self.location_queue = list(self.user_locations.items())
            self.process_next_location()

    def process_next_location(self):
        if not self.location_queue:
            self.location_queue = list(self.user_locations.items())

        if self.location_queue:
            user, location = self.location_queue.pop(0)
            self.check_weather_for_location(user, location)

        if hasattr(self, 'weather_check_timer'):
            self.weather_check_timer.cancel()

        self.weather_check_timer = threading.Timer(self.check_interval, self.process_next_location)
        self.weather_check_timer.start()

    def check_weather_for_location(self, user, location):
        current_time = time.time()
        if location in self.alert_cooldown and current_time - self.alert_cooldown[location] < self.alert_cooldown_period:
            return

        saved_location = self.user_locations.get(user)
        if saved_location:
            if saved_location.isdigit() and len(saved_location) == 5:
                weather_data = self.get_weather(saved_location)
                forecast_data = self.get_forecast(saved_location)
            else:
                lat, lon, _ = self.get_coordinates(saved_location)
                weather_data = self.get_weather_by_lat_lon(lat, lon)
                forecast_data = self.get_forecast_by_lat_lon(lat, lon)

            if 'error' in weather_data:
                return

            alerts = weather_data.get('alerts', [])
            if alerts:
                self.alert_cooldown[location] = current_time
                for alert in alerts:
                    for channel in self.channels_to_join + self.dynamic_channels:
                        self.announce_alert(channel, user, saved_location, alert)

    def fetch_weather_alerts(self, lat, lon):
        url = f"http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,daily&appid={self.weather_api_key}&alerts"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get('alerts', [])
        except requests.RequestException as e:
            print(f"Error fetching weather alerts: {e}")
        return []

    def announce_alert(self, channel, user, full_location_name, alert):
        base_message = f"🚨 {user}, alert for {full_location_name}: {alert['event']} - "
        description = alert['description'].replace('\n', ' ').replace('\r', ' ')

        max_length = 512 - len(base_message) - len(channel) - 30
        if len(description) > max_length:
            parts = [description[i:i + max_length] for i in range(0, len(description), max_length)]
            for part in parts:
                message = base_message + part
                self.connection.privmsg(channel, message)
        else:
            message = base_message + description
            self.connection.privmsg(channel, message)

    def on_pubmsg(self, c, e):
        message = e.arguments[0].strip()
        source = e.source.nick
        channel = e.target

        if message.startswith('!w '):
            parts = message.split(' ', 1)
            query = parts[1].strip() if len(parts) > 1 else self.user_locations.get(source)

            if query:
                if query.isdigit() and len(query) == 5:
                    location = query
                    weather_data = self.get_weather(query)
                    forecast_data = self.get_forecast(query)
                else:
                    lat, lon, resolved_location = self.get_coordinates(query)
                    if lat and lon:
                        weather_data = self.get_weather_by_lat_lon(lat, lon)
                        forecast_data = self.get_forecast_by_lat_lon(lat, lon)
                        location = resolved_location
                    else:
                        c.privmsg(channel, f"{source}: Could not resolve location '{query}'.")
                        return

                if 'error' in weather_data:
                    c.privmsg(channel, f"{source}: Error retrieving weather for {location}.")
                    return

                weather_response = self.format_weather(weather_data)
                forecast_response = self.format_forecast(forecast_data)
                c.privmsg(channel, f"{source}: {weather_response} | {forecast_response}")
            else:
                c.privmsg(channel, f"{source}: Please provide a location after the !w command or set your location with !setweather.")

        elif message.startswith('!w'):
            location = self.user_locations.get(source)
            if location:
                if location.isdigit() and len(location) == 5:
                    weather_data = self.get_weather(location)
                    forecast_data = self.get_forecast(location)
                else:
                    lat, lon, _ = self.get_coordinates(location)
                    weather_data = self.get_weather_by_lat_lon(lat, lon)
                    forecast_data = self.get_forecast_by_lat_lon(lat, lon)

                if 'error' in weather_data:
                    c.privmsg(channel, f"{source}: Error retrieving weather for {location}.")
                    return

                weather_response = self.format_weather(weather_data)
                forecast_response = self.format_forecast(forecast_data)
                c.privmsg(channel, f"{source}: {weather_response} | {forecast_response}")
            else:
                c.privmsg(channel, f"{source}: Please set your location with !setweather <zip or location>.")

        elif message.startswith('!setweather '):
            parts = message.split(' ', 1)
            if len(parts) == 2:
                location_query = parts[1].strip()

                if location_query.isdigit() and len(location_query) == 5:
                    self.user_locations[source] = location_query
                    self.save_data('user_locations.json', self.user_locations)
                    c.privmsg(channel, f"{source}: Weather location set to {location_query} (zip code).")
                else:
                    lat, lon, full_location_name = self.get_coordinates(location_query)
                    if lat and lon:
                        city_country = ', '.join(full_location_name.split(', ')[:2])
                        self.user_locations[source] = city_country
                        self.save_data('user_locations.json', self.user_locations)
                        c.privmsg(channel, f"{source}: Weather location set to {city_country}.")
                    else:
                        c.privmsg(channel, f"{source}: Could not find location for '{location_query}'. Usage: !setweather <zip or location>")
            else:
                c.privmsg(channel, f"{source}: Incorrect usage of !setweather. Usage: !setweather <zip or location>")

        elif message.startswith('!check '):
            parts = message.split(' ', 1)
            if len(parts) == 2:
                nick_to_check = parts[1].strip()
                location = self.user_locations.get(nick_to_check)

                if location:
                    if location.isdigit() and len(location) == 5:
                        weather_data = self.get_weather(location)
                        forecast_data = self.get_forecast(location)
                    else:
                        lat, lon, _ = self.get_coordinates(location)
                        weather_data = self.get_weather_by_lat_lon(lat, lon)
                        forecast_data = self.get_forecast_by_lat_lon(lat, lon)

                    if 'error' in weather_data:
                        c.privmsg(channel, f"{source}: Error retrieving weather for {location}.")
                        return

                    weather_response = self.format_weather(weather_data)
                    forecast_response = self.format_forecast(forecast_data)
                    c.privmsg(channel, f"{nick_to_check}: {weather_response} | {forecast_response}")
                else:
                    c.privmsg(channel, f"{source}: No location found for {nick_to_check}. Please ensure the location is set with !setweather.")
            else:
                c.privmsg(channel, f"{source}: Please specify a nickname to check the weather for, using !check <nick>.")

        elif message.startswith('!join '):
            if source not in ['gh0st', 'n0ne`']:
                c.privmsg(channel, f"{source}: You do not have permission to use this command.")
                return

            parts = message.split(' ', 1)
            if len(parts) == 2:
                new_channel = parts[1].strip()
                if new_channel.startswith('#'):
                    c.join(new_channel)
                    if new_channel not in self.dynamic_channels:
                        self.dynamic_channels.append(new_channel)
                        self.save_data('dynamic_channels.json', self.dynamic_channels)
                    c.privmsg(channel, f"{source}: Joined {new_channel}")
                else:
                    c.privmsg(channel, f"{source}: Invalid channel name '{new_channel}'. Channel names must start with '#'.")
            else:
                c.privmsg(channel, f"{source}: Incorrect usage of !join. Usage: !join <#channel>")

        elif message.startswith('!part '):
            if source not in ['gh0st', 'n0ne`']:
                c.privmsg(channel, f"{source}: You do not have permission to use this command.")
                return

            parts = message.split(' ', 1)
            if len(parts) == 2:
                part_channel = parts[1].strip()
                if part_channel in self.dynamic_channels:
                    self.dynamic_channels.remove(part_channel)
                    self.save_data('dynamic_channels.json', self.dynamic_channels)
                c.part(part_channel)
                c.privmsg(channel, f"{source}: Left {part_channel}")
            else:
                c.privmsg(channel, f"{source}: Incorrect usage of !part. Usage: !part <#channel>")

        elif message.startswith('!help'):
            self.show_help(c, channel, source)

        else:
            return

    def show_help(self, c, channel, source):
        help_messages = [
            "TwistedWeather Bot by gh0st:",
            "!w <location> - Get the current weather for the specified location.",
            "!w - Get the current weather for your saved location.",
            "!check <nick> - Check the weather for the saved location of the specified nickname.",
            "!setweather <zip or location> - Set your weather location using a zip code or location name.",
            "!join <#channel> - Make the bot join the specified channel.",
            "!part <#channel> - Make the bot leave the specified channel.",
            "!help - Show this help message."
        ]
        for message in help_messages:
            c.privmsg(channel, f"{source}: {message}")

    def get_weather_by_lat_lon(self, lat, lon):
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={self.weather_api_key}"
        return self.fetch_data(url)

    def get_forecast_by_lat_lon(self, lat, lon):
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={self.weather_api_key}"
        return self.fetch_data(url)

    def fetch_data(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
        return {"error": "Error fetching data"}

    def get_weather(self, query):
        if not query:
            return {"error": "No location set. Use !setweather to set your location."}

        query_type = 'q' if ',' in query else 'zip'
        url = f"http://api.openweathermap.org/data/2.5/weather?{query_type}={query}&units=metric&appid={self.weather_api_key}"
        return self.fetch_data(url)

    def get_forecast(self, query):
        if not query:
            return {"error": "No location set. Use !setweather to set your location."}

        query_type = 'q' if ',' in query else 'zip'
        url = f"http://api.openweathermap.org/data/2.5/forecast?{query_type}={query}&units=metric&appid={self.weather_api_key}"
        return self.fetch_data(url)

    def format_weather(self, weather_data):
        try:
            city = weather_data['name']
            country = weather_data['sys']['country']
            temp_c = round(weather_data['main']['temp'])
            high_temp_c, low_temp_c = self.get_day_high_low(weather_data['coord']['lat'], weather_data['coord']['lon'])
            if high_temp_c is None or low_temp_c is None:
                high_temp_c = weather_data['main']['temp_max']
                low_temp_c = weather_data['main']['temp_min']
            temp_f = round(temp_c * 9 / 5 + 32)
            high_temp_f = round(high_temp_c * 9 / 5 + 32)
            low_temp_f = round(low_temp_c * 9 / 5 + 32)
            humidity = weather_data['main']['humidity']
            wind_speed_mps = weather_data['wind']['speed']
            wind_speed_mph = round(wind_speed_mps * 2.237)
            wind_direction_deg = weather_data['wind']['deg']
            wind_direction = self.degrees_to_cardinal(wind_direction_deg)
            weather = weather_data['weather'][0]['description']
            weather_symbol = self.get_weather_symbol(weather_data['weather'][0]['id'])

            city_country = f"\x03{self.random_color()}{city}, {country}\x03"
            current_temp = f"\x02Weather in\x02 {city_country}: \x03{self.get_temp_color(temp_f)}{temp_f}°F / {temp_c}°C\x03"
            high_low_temp = f"High: \x03{self.get_temp_color(high_temp_f)}{high_temp_f}°F / {high_temp_c}°C\x03, " \
                            f"Low: \x03{self.get_temp_color(low_temp_f)}{low_temp_f}°F / {low_temp_c}°C\x03"
            weather_desc = f"\x03{self.random_color()}{weather} {weather_symbol}\x03"
            humidity_str = f"\x03{self.random_color()}Humidity: {humidity}%\x03"
            wind_str = f"\x03{self.random_color()}Wind: {wind_speed_mph}mph {wind_direction}\x03"

            return f"{current_temp}, {high_low_temp}, {weather_desc}, {humidity_str}, {wind_str}"
        except KeyError:
            return "Try using your zip code. !w + zipcode. --- Save your location: !setweather + nick + zipcode"

    def get_day_high_low(self, lat, lon):
        forecast_data = self.get_forecast_by_lat_lon(lat, lon)
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        today_forecasts = [
            f for f in forecast_data['list']
            if f['dt_txt'].startswith(today_str)
        ]
        if not today_forecasts:
            return None, None
        high_temp_c = max(f['main']['temp_max'] for f in today_forecasts)
        low_temp_c = min(f['main']['temp_min'] for f in today_forecasts)
        return high_temp_c, low_temp_c

    def degrees_to_cardinal(self, degrees):
        val = int((degrees / 22.5) + 0.5)
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        return directions[(val % 16)]

    def format_forecast(self, forecast_data):
        try:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')
            next_day_forecasts = [
                f for f in forecast_data['list']
                if f['dt_txt'].startswith(tomorrow_str)
            ]

            if next_day_forecasts:
                avg_temp_c = round(sum(f['main']['temp'] for f in next_day_forecasts) / len(next_day_forecasts))
                high_temp_c = round(max(f['main']['temp_max'] for f in next_day_forecasts))
                low_temp_c = round(min(f['main']['temp_min'] for f in next_day_forecasts))
                avg_temp_f = round(avg_temp_c * 9 / 5 + 32)
                high_temp_f = round(high_temp_c * 9 / 5 + 32)
                low_temp_f = round(low_temp_c * 9 / 5 + 32)
                weather_description = next_day_forecasts[0]['weather'][0]['description']
                weather_symbol = self.get_weather_symbol(next_day_forecasts[0]['weather'][0]['id'])

                forecast_summary = f"\x02Tomorrow's forecast:\x02 \x03{self.get_temp_color(avg_temp_f)}{avg_temp_f}°F / {avg_temp_c}°C\x03"
                high_low_temp = f"High: \x03{self.get_temp_color(high_temp_f)}{high_temp_f}°F / {high_temp_c}°C\x03, " \
                                f"Low: \x03{self.get_temp_color(low_temp_f)}{low_temp_f}°F / {low_temp_c}°C\x03"
                weather_desc = f"\x03{self.random_color()}{weather_description} {weather_symbol}\x03"

                return f"{forecast_summary}, {high_low_temp}, {weather_desc}"
            else:
                return "No forecast data available for tomorrow."
        except KeyError:
            return "Could not retrieve forecast data."

    def get_weather_symbol(self, weather_id):
        if weather_id >= 200 and weather_id < 300:
            return "⛈️"
        elif weather_id >= 300 and weather_id < 600:
            return "🌧️"
        elif weather_id >= 600 and weather_id < 700:
            return "❄️"
        elif weather_id >= 700 and weather_id < 800:
            return "🌫️"
        elif weather_id == 800:
            return "☀️"
        else:
            return "☁️"

    def random_color(self):
        return random.choice(['03', '04', '07', '08', '09', '10', '11', '12', '13', '14', '15'])

    def get_temp_color(self, temp_f):
        if temp_f >= 90:
            return '05'
        elif temp_f >= 80:
            return '04'
        elif temp_f >= 70:
            return '07'
        elif temp_f >= 60:
            return '08'
        elif temp_f >= 50:
            return '03'
        elif temp_f >= 32:
            return '10'
        else:
            return '12'

    def save_data(self, filename, data):
        with open(filename, 'w') as file:
            json.dump(data, file)

    def load_data(self, filename, expected_type):
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, expected_type):
                    return data
                else:
                    return expected_type()
        except (FileNotFoundError, json.JSONDecodeError):
            return expected_type()

    def on_disconnect(self, c, e):
        time.sleep(5)
        self.jump_server()

def main():
    server = "irc.twistednet.org"
    channels = ["#dev", "#twisted"]
    nickname = "w"
    weather_api_key = "PUT API KEY HERE"
    geocoding_api_key = "PUT API KEY HERE"

    bot = GhostBot(channels, nickname, server, weather_api_key=weather_api_key, geocoding_api_key=geocoding_api_key)
    bot.start()

if __name__ == "__main__":
    main()
