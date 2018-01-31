import os
import logging
from flask import request, Flask
import json

from jinja2 import Template

from common import Age
from globals import SERVER_HOST, SERVER_PORT
from nudgebot.db import db
from nudgebot import NudgeBot
from nudgebot.lib.github import GithubEnv
from nudgebot.events_handler import EventsHandler


logging.basicConfig()
logger = logging.getLogger('ServerLogger')
logger.setLevel(logging.INFO)

app = Flask(__name__)


@app.route('/webhooks', methods=['POST'])
def webhook_event():
    payload = (request.json if request.json else json.loads(request.form['payload']))
    NudgeBot().process_github_event(payload)
    return 'OK'


@app.route('/statistics', methods=['GET'])
def statistics_page():
    with open('{}/statistics.j2'.format(os.path.dirname(__file__)), 'r') as f:
        template = Template(f.read().encode('UTF-8'))
    stats = [stat for stat in db().pr_stats.find()]
    # Temp wrapper for aging - TODO: do this internally in the stat class!!!
    for stat in stats:
        for key in ('last_update', 'age'):
            stat[key] = Age(stat[key])
    html = template.render(stats=stats, repos=GithubEnv().repos)
    return html


def run():
    logger.info('Stating server')
    if not db().initialization_time:
        NudgeBot().initialize()
    events_handler = EventsHandler()
    events_handler.start()
    logger.info('Running server...')
    app.run(host=SERVER_HOST, port=SERVER_PORT)
