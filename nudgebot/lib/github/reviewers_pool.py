import logging

from cached_property import cached_property

from config import config
from nudgebot.lib.github.users import ReviewerUser
from nudgebot.db import db


logging.basicConfig()
logger = logging.getLogger('ReviewersPoolLogger')
logger.setLevel(logging.INFO)


class ReviewersPool(object):

    def __init__(self, repository):
        self._repository = repository
        self.reload_db()

    @cached_property
    def repository(self):
        return self._repository

    @property
    def pool(self):
        return self._pool

    def get_reviewers(self, level=-1):
        out = []
        for login in self._pool:
            if level == -1:
                out.append(login)
            elif self._pool[login]['level'] == level:
                out.append(login)
        return out

    @property
    def reviewers(self):
        return self.get_reviewers()

    def get_level(self, reviewer):
        if reviewer not in self._pool:
            # TODO: define appropriate exception
            raise Exception('Reviewer not found in the pool: {}'.format(reviewer))
        return self._pool[reviewer]['level']

    def initialize(self):
        logger.info('Initializing Reviewers pool of repository "{}"...'.format(self.repository.name))
        repo_pulls = self._repository.get_pull_requests()
        for level, logins in enumerate(self._repository.config.reviewers):
            level += 1
            for login in logins:
                if login in self._pool:
                    self._pool[login]['level'] = level
                else:
                    self._pool[login] = {'level': level, 'pull_requests': []}

            for pull_request in repo_pulls:
                for reviewer in pull_request.reviewers:
                    if reviewer.login not in self._pool:
                        continue
                    self.attach_pr_to_reviewer(reviewer.login, pull_request.number)
        self.update_db()

    def update_db(self):
        # We are copying the dict in order to prevent the addition of '_id'
        if not db().reviewers_pool.find_one():
            db().reviewers_pool.insert_one(self._pool.copy())
            return
        db().reviewers_pool.update({}, self._pool.copy())

    def reload_db(self):
        pool = db().reviewers_pool.find_one({})
        if pool:
            del pool['_id']
            self._pool = pool
        else:
            self._pool = {}
            self.update_db()

    def update_from_pr_stats(self, pr_stats):
        """Updating the pool from according to the pull request statistics"""
        stat_reviewers = [r.login for r in pr_stats.reviewers()]
        for login in self.reviewers:
            pr_merged = pr_stats.pull_request.state != 'open'
            already_attached = pr_stats.number() in self._pool[login]['pull_requests']
            reviewer_was_set = login in stat_reviewers
            if already_attached and (not reviewer_was_set or pr_merged):
                self.attach_pr_to_reviewer(login, pr_stats.number(), detach=True)
            elif not already_attached and reviewer_was_set:
                self.attach_pr_to_reviewer(login, pr_stats.number())

    def pull_reviewer(self, level, pull_request):
        """Pulling a reviewer and update the pool"""
        # TODO: pull formula
        reviewers = filter(lambda r: (r[0] not in pull_request.reviewers
                                      and r[0] != pull_request.owner.login
                                      and r[1]['level'] == level), self._pool.items())
        reviewer = min(reviewers, key=lambda rev: len(rev[1]['pull_requests']))
        if not reviewer:
            raise Exception()  # TODO: Define appropriate exception
        if not config().config.testing_mode:
            self.attach_pr_to_reviewer(reviewer[0], pull_request.number)
        return ReviewerUser(reviewer[0])

    def attach_pr_to_reviewer(self, reviewer_login, pull_request_number, detach=False):
        pull_request_number = int(pull_request_number)
        if reviewer_login not in self._pool:
            raise Exception()  # TODO: Define appropriate exception
        already_attached = pull_request_number in self._pool[reviewer_login]['pull_requests']
        if detach and already_attached:
            self._pool[reviewer_login]['pull_requests'].remove(pull_request_number)
        elif not detach and not already_attached:
            self._pool[reviewer_login]['pull_requests'].append(pull_request_number)
        self.update_db()  # TODO: update the relevant field instead of update all
