import asyncio
import aiohttp
from flask import Flask, jsonify, render_template
from aiohttp import ClientError, ClientTimeout
import pytz
import logging
import json

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='templates', static_folder='assets')

async def fetch_json(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

status_data = {}

async def fetch_status(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            return url, 'UP' if response.status == 200 else 'DOWN'
    except (ClientError, asyncio.TimeoutError):
        return url, 'UNKNOWN'
    except Exception as e:
        logging.error(f"Error checking {url}: {e}")
        return url, 'DOWN'

async def check_website_status(url_group):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_status(session, url) for url in url_group]
        results = await asyncio.gather(*tasks)
        for url, status in results:
            status_data[url] = status

async def periodic_task():
    while True:
        await asyncio.sleep(20)
        await schedule_checks()

async def schedule_checks():
    up_urls = [url for url, status in status_data.items() if status == 'UP']
    down_urls = [url for url, status in status_data.items() if status == 'DOWN']
    unknown_urls = [url for url, status in status_data.items() if status == 'UNKNOWN']
    await check_website_status(up_urls)
    await check_website_status(down_urls)
    await check_website_status(unknown_urls)

@app.route('/api/website', methods=['GET'])
def get_websites():
    return jsonify(data_json)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(status_data)

@app.route('/')
def index():
    return render_template('webMonitoring.html')

if __name__ == "__main__":
    data_json = asyncio.run(fetch_json('assets/website.json'))
    urls = {data_web['url']: 'UNKNOWN' for data_web in data_json['data']}
    asyncio.run(check_website_status(urls.keys()))

    asyncio.ensure_future(periodic_task())
    app.run(port=1000)
