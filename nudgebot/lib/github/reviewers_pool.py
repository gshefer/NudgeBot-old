from cached_property import cached_property

from nudgebot.lib.github.users import ReviewerUser
from nudgebot.db import db


class ReviewersPool(object):

    def __init__(self, repository):
        self._repository = repository
        self._pool = {}

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
        db().reviewers_pool.remove()
        # We are copying the dict in order to prevent the addition of '_id'
        db().reviewers_pool.insert_one(self._pool.copy())

    def pull_reviewer(self, level, pull_request):
        """Pulling a reviewer and update the pool"""
        # TODO: pull formula
        reviewers = filter(lambda r: (r[0] not in pull_request.reviewers
                                      and r[0] != pull_request.owner.login
                                      and r[1]['level'] == level), self._pool.items())
        reviewer = min(reviewers, key=lambda rev: len(rev[1]['pull_requests']))
        if not reviewer:
            raise Exception()  # TODO: Define appropriate exception
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
