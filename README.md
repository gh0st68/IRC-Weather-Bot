<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twisted Weather Bot By Gh0st</title>
</head>
<body>
    <h1>Twisted Weather Bot By Gh0st</h1>

    <h2>Requirements</h2>
    <p>To run this bot, you need to obtain two API keys:</p>
    <ol>
        <li><strong>OpenWeather API Key</strong>: <a href="https://openweathermap.org/" target="_blank">OpenWeather API Key</a></li>
        <li><strong>OpenCage API Key</strong>: <a href="https://opencagedata.com/" target="_blank">OpenCage API Key</a></li>
    </ol>
    <p>Both of these API keys are free.</p>

    <h2>Installation</h2>
    <ol>
        <li>
            <strong>Install Required Libraries</strong><br>
            You need to install the required libraries for the bot. Run the following commands:
            <pre><code>pip3 install irc.bot
pip3 install ssl
pip3 install requests
pip3 install jaraco.stream
            </code></pre>
        </li>
        <li>
            <strong>Save the Script</strong><br>
            Save the bot script to a file named <code>TwistedWeatherBot.py</code>.
        </li>
        <li>
            <strong>Edit the Script</strong><br>
            Edit the script to add your API keys:
            <pre><code>weather_api_key = "your_openweather_api_key"
geocoding_api_key = "your_opencage_api_key"
            </code></pre>
        </li>
    </ol>

    <h2>Running the Bot</h2>
    <p>To keep the bot running even when you close the console, it is recommended to use <code>screen</code>.</p>
    <ol>
        <li>
            <strong>Start a Screen Session</strong><br>
            Open a screen session named <code>weatherbot</code>:
            <pre><code>screen -S weatherbot</code></pre>
        </li>
        <li>
            <strong>Run the Bot</strong><br>
            Within the screen session, run the bot:
            <pre><code>python3 TwistedWeatherBot.py</code></pre>
        </li>
        <li>
            <strong>Detach the Screen Session</strong><br>
            Detach from the screen session to keep the bot running in the background:
            <pre><code>Ctrl + A + D</code></pre>
        </li>
        <li>
            <strong>Reattach to the Screen Session</strong><br>
            To reattach to the screen session:
            <pre><code>screen -r weatherbot</code></pre>
        </li>
    </ol>

    <h2>Bot Commands</h2>

    <h3>Triggers for the Bot</h3>
    <ul>
        <li><code>!w &lt;location&gt;</code>: Get the current weather for the specified location.
            <ul>
                <li>Example: <code>!w NYC</code></li>
            </ul>
        </li>
        <li><code>!weather &lt;location&gt;</code>: Alias for <code>!w &lt;location&gt;</code>.
            <ul>
                <li>Example: <code>!weather NYC</code></li>
            </ul>
        </li>
    </ul>

    <h3>Commands</h3>
    <ul>
        <li><code>!w &lt;location&gt;</code>: Get the current weather for the specified location.
            <ul>
                <li>Example: <code>!w NYC</code></li>
            </ul>
        </li>
        <li><code>!w</code>: Get the current weather for your saved location.</li>
        <li><code>!check &lt;nick&gt;</code>: Check the weather for the saved location of the specified nickname.
            <ul>
                <li>Example: <code>!check username</code></li>
            </ul>
        </li>
        <li><code>!setweather &lt;zip or location&gt;</code>: Set your weather location using a zip code or location name.
            <ul>
                <li>Example: <code>!setweather 10001</code></li>
            </ul>
        </li>
        <li><code>!join &lt;#channel&gt;</code>: Make the bot join the specified channel.
            <ul>
                <li>Example: <code>!join #weather</code></li>
            </ul>
        </li>
        <li><code>!part &lt;#channel&gt;</code>: Make the bot leave the specified channel.
            <ul>
                <li>Example: <code>!part #weather</code></li>
            </ul>
        </li>
        <li><code>!help</code>: Show the help message.</li>
    </ul>

    <h2>Questions or Help</h2>
    <p>For questions, help, or to visit, join us at:</p>
    <h3>IRC.TWISTEDNET.ORG CHANNEL #DEV & #TWISTED</h3>
</body>
</html>
