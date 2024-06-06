import asyncio
import aiohttp
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import atexit
import logging
import json

logging.basicConfig(level=logging.INFO)
app = Flask(__name__, template_folder='templates', static_folder='assets')


def fetch_json(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data


file_json = 'assets/website.json'
data_json = fetch_json(file_json)
webUrls = {dataWeb['url']: 'Warning' for dataWeb in data_json['data']}

statusData = {}


async def fetch_status(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            return url, 'Up' if response.status == 200 else 'Down'
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return url, 'Warning'
    except Exception as e:
        logging.error(f"Error checking {url}: {e}")
        return url, 'Down'


async def check_website_status(urlGroup):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_status(session, url) for url in urlGroup]
        results = await asyncio.gather(*tasks)
        for url, status in results:
            statusData[url] = status


def schedule_checks():
    upUrls = [url for url, status in statusData.items() if status == 'Up']
    downUrls = [url for url, status in statusData.items()
                if status == 'Down']
    unknownUrls = [url for url, status in statusData.items()
                    if status == 'Warning']

    asyncio.run(check_website_status(upUrls))
    asyncio.run(check_website_status(downUrls))
    asyncio.run(check_website_status(unknownUrls))


scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(func=lambda: asyncio.run(
    check_website_status(webUrls.keys())), trigger="interval", seconds=60)
scheduler.add_job(func=lambda: schedule_checks(),
                trigger="interval", seconds=10)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


@app.route('/api/website', methods=['GET'])
def get_websites():
    return jsonify(data_json)


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(statusData)


@app.route('/')
def index():
    return render_template('webMonitoring.html')


if __name__ == "__main__":
    asyncio.run(check_website_status(webUrls.keys()))
    app.run(port=8000)
