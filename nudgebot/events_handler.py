import threading
import requests
import github
import time
import logging
from datetime import datetime

from common import Singleton, as_local_time
from nudgebot.lib.github import GithubEnv
from config import config
from nudgebot.db import db
from nudgebot.globals import SERVER_PORT


logging.basicConfig()
logger = logging.getLogger('EventsHandlerLogger')
logger.setLevel(logging.INFO)


class EventsHandler(threading.Thread):
    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.daemon = True
        self._last_check = None

    def check_github_events(self):
        """Sending new Github events to the webhooks server"""
        for repo in GithubEnv().repos:
            logger.info('Searching for new event in repository "{}"'.format(repo.name))
            for getter in ('get_events', 'get_issues_events'):
                for event in getattr(repo, getter)():
                    is_this_new = (as_local_time(event.last_modified or event.created_at,
                                                 raise_if_native_time=False)
                                   < db().initialization_time)
                    is_this_me = event.actor.login == config().credentials.github.username
                    if (event.id in db().delivered_github_events or is_this_new or is_this_me):
                        break
                    logger.info('New event detected: id={}'.format(event.id))
                    if isinstance(event, github.IssueEvent.IssueEvent):
                        payload = event.raw_data
                    else:
                        payload = event.payload
                    # Fill some required fields that could be missing in the events API but
                    # coming with webhooks for some reason
                    payload['sender'] = {'login': event.actor.login}
                    payload['repository'] = payload.get('repository', {'name': repo.name})
                    requests.post('http://localhost:{}/webhooks'.format(SERVER_PORT), json=payload)
                    db().add_delivered_github_event(event.id)

    def run(self):
        logger.info('Starting events handler.')
        while True:
            if (not self._last_check or ((datetime.now() - self._last_check).total_seconds() >
                                         config().config.events_handler.check_timeout_seconds)):
                self._last_check = datetime.now()
                if config().config.events_handler.use_github_events_proxy:
                    self.check_github_events()
            else:
                time.sleep(1)
