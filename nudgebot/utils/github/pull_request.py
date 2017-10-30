# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
import json
import re

import dateparser
import requests

from . import env
from config import conf


class PullRequestTag(object):
    """Represents Pull Request title tag.
    e.g. [RFR], [WIP], ...
    """
    @classmethod
    def fetch(cls, title):
        """PullRequestTitleTag Factory - fetching tags from title.
        Args:
            * title (str): the Pull request title.
        Returns: list of PullRequestTitleTag
        """
        assert isinstance(title, basestring)
        detected_tags = []
        for tag_type, data in conf().github.pull_request_title_tags.items():
            tag_names = re.findall(data.pattern, title)
            for tag_name in tag_names:
                if tag_name in data.options:
                    detected_tags.append(
                        cls(tag_type, tag_name)
                    )
        return detected_tags

    def __init__(self, tag_type, tag_name):
        assert isinstance(tag_type, basestring)
        assert isinstance(tag_name, basestring)
        self._tag_type = tag_type
        self._tag_name = tag_name

    def __eq__(self, other):
        return (self.type == getattr(other, 'type', None) and
                self.name == getattr(other, 'name', None))

    def __repr__(self, *args, **kwargs):
        return '<{} type="{}" name="{}">'.format(
            self.__class__.__name__, self.type, self.name)

    @property
    def type(self):
        return self._tag_type

    @property
    def name(self):
        return self._tag_name

    @property
    def json(self):
        return {'type': self.type, 'name': self.name}


class PullRequest(object):
    """Pull Request includes a bunch of the properties and the information
    about the pull request.
    """
    def __init__(self, org, repo, json_data):

        self.org = org
        self.repo = repo
        self._json_data = json_data

    @classmethod
    def get_all(cls, **filters):
        """
        Args (filters):
            * state (optional): (str) the state of the pull requests to grab (open || closed).
            * logins (optional): (list || tuple) a list of the logins.
            * repos (optional): (list || tuple) a list of the repos.
        """
        state = filters.get('state', 'open')
        logins = [login.lower() for login in filters.get('logins', [])]
        repos = filters.get('repos', env().repos)
        prs = []
        for repo in repos:
            for pr in repo.get_pulls(state=state):
                if logins and pr.user.login.lower() not in logins:
                    continue
                prs.append(cls(repo.organization.name, repo.name, pr))
        return prs

    def judge(self):
        lrc = self.last_review_comment
        if not lrc:
            return
        pr_inactivity_timeout = timedelta(conf().github.pr_inactivity_timeout.days,
                                          conf().github.pr_inactivity_timeout.hours)
        pr_inactivity_time = datetime.now() - lrc.created_at
        if pr_inactivity_time > pr_inactivity_timeout:
            return ('PR#{} is waiting for review for {} days and {} hours: {}'
                    .format(self.number, pr_inactivity_time.days,
                            pr_inactivity_time.seconds / 3600, self.url))

    @property
    def state_history(self):
        # TODO: Returns: {<date>: <state>, ...}
        pass

    @property
    def json_data(self):
        return self._json_data

    @property
    def url(self):
        return self.json_data.url

    @property
    def html(self):
        return requests.get(self._json_data.html_url).content

    @property
    def patch_url(self):
        return self._json_data.patch_url

    @property
    def diff_url(self):
        return self._json_data.diff_url

    @property
    def patch(self):
        return requests.get(self._json_data.patch_url).content.encode('UTF-8')

    @property
    def diff(self):
        return requests.get(self._json_data.diff_url).content.encode('UTF-8')

    @property
    def number(self):
        return self._json_data.number

    @property
    def user(self):
        return getattr(self._json_data.user, 'name',
                       self._json_data.user.login)

    @property
    def title(self):
        return self._json_data.title

    @property
    def tags(self):
        return PullRequestTag.fetch(self.title)

    @property
    def age(self):
        now = datetime.now()
        return now - self._json_data.created_at

    @property
    def review_comments(self):
        comments = [c for c in self._json_data.get_review_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def last_review_comment(self):
        review_comments = self.review_comments
        if review_comments:
            return max(review_comments, key=lambda item: item.updated_at)

    @property
    def comments(self):
        comments = [c for c in self._json_data.get_issue_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def test_results(self):
        tests = json.loads(requests.get(self._json_data.raw_data['statuses_url']).content)
        out = {}
        for test in tests:
            out[test['context']] = test['description']
        return out

    @property
    def owner(self):
        return self._json_data.user

    @property
    def last_code_update(self):
        return dateparser.parse(list(self._json_data.get_commits()).pop().last_modified)

    @property
    def json(self):
        """Get the object data as dictionary"""
        lst_cmnt = self.last_review_comment
        age_total_seconds = int(self.age.total_seconds())
        days_ago = age_total_seconds / 86400
        hours_ago = (age_total_seconds - days_ago * 86400) / 3600
        out = {
            'org': self.org,
            'repo': self.repo,
            'number': self.number,
            'owner': self.owner.name or self.owner.login,
            'title': self.title,
            'tags': [tag.json for tag in self.tags],
            'age': {
                'days': days_ago,
                'hours': hours_ago
            },
            'tests': self.test_results,
            'last_code_update': self.last_code_update.isoformat()
        }
        if lst_cmnt:
            out['last_review_comment'] = {
                'user': lst_cmnt.user.name or lst_cmnt.user.login,
                'body': lst_cmnt.body,
                'updated_at': lst_cmnt.updated_at.isoformat()
            }
        return out
