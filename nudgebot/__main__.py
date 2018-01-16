from flask import request, Flask
import json
import github

from nudgebot import NudgeBot
from config import config
from nudgebot.website import WebSite


if config().config.debug_mode:
    github.enable_console_debug_logging()


app = Flask(__name__)
nudge_bot = NudgeBot()


@app.route('/webhooks', methods=['POST'])
def webhook_event():
    nudge_bot.process_github_event(json.loads(request.form['payload']))
    return 'OK'


@app.route('/statistics', methods=['GET'])
def statistics_page():
    return WebSite().statistics_html


if __name__ == '__main__':
    nudge_bot.initialize()
    app.run(host='0.0.0.0', port=8080)
