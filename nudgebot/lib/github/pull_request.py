# -*- coding: utf-8 -*-
from datetime import datetime
import json
import re

from cached_property import cached_property
import dateparser
import requests

from .users import User, ContributorUser, ReviewerUser
from config import config
from common import ExtendedEnum


class PRtag(ExtendedEnum):
    NOTEST = 'NOTEST'
    NOMERGE = 'NOMERGE'
    LP1 = '1LP'
    LP2 = '2LP'
    LP3 = '3LP'


class PRstate(ExtendedEnum):
    WIP = 'WIP'
    BLOCKED = 'BLOCKED'
    WIPTEST = 'WIPTEST'
    RFR = 'RFR'


class ReviewCommentThread(object):

    def __init__(self, pull_request, comments):
        assert isinstance(comments, list) and len(comments)
        self._comments = comments
        self._pull_request = pull_request

    def __repr__(self, *args, **kwargs):
        return '<{} pull_request={} path="{}" line="{}">'.format(
            self.__class__.__name__, self._pull_request.number, self.path, self.line)

    def add_comment(self, comment):
        # TODO: Raise if the comment is not in the same pr/path/line
        self._comments.append(comment)

    @property
    def issue_comments(self):
        return sorted(self._comments, key=lambda c: c.created_at)

    @property
    def first_comment(self):
        return self.issue_comments[0]

    @property
    def last_comment(self):
        return self.issue_comments[-1]

    @cached_property
    def path(self):
        return self._comments[0].path

    @cached_property
    def line(self):
        return self._comments[0].position or self._comments[0].original_position

    @property
    def outdated(self):
        return self._comments[0].position is None

    @classmethod
    def fetch_threads(cls, pull_request):
        threads = {}
        for comment in pull_request.review_comments:
            key = '{}:{}'.format(comment.path, comment.original_position)
            if key in threads:
                threads[key].add_comment(comment)
            else:
                threads[key] = cls(pull_request, [comment])
        return threads.values()


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
        tag_names = re.findall(config().config.github.pull_request_title_tag.pattern, title)
        for tag_name in tag_names:
            tag_name = tag_name.upper()
            if tag_name in PRtag.values():
                tag = PRtag.get_by_value(tag_name)
            elif tag_name in PRstate.values():
                tag = PRstate.get_by_value(tag_name)
            else:
                raise Exception()  # TODO: Define appropriate exception
            detected_tags.append(cls(tag))
        return detected_tags

    def __init__(self, tag):
        assert isinstance(tag, (PRtag, PRstate))
        self._tag = tag

    def __eq__(self, other):
        return self._tag == getattr(other, '_tag', None)

    def __repr__(self, *args, **kwargs):
        return '<{} type="{}" name="{}">'.format(
            self.__class__.__name__, self.type, self.name)

    @property
    def type(self):
        return self._tag.__class__

    @property
    def name(self):
        return self._tag.value

    @property
    def raw(self):
        return config().config.github.pull_request_title_tag.format.format(self.name)

    @property
    def json(self):
        return {'type': self.type, 'name': self.name, 'raw': self.raw}


class PullRequest(object):
    """Pull Request includes a bunch of the properties and the information
    about the pull request.
    """
    def __init__(self, repo, github_obj):

        self.repo = repo
        self._github_obj = github_obj

    def __repr__(self, *args, **kwargs):
        return '<{} number="{}" title="{}" user="{}">'.format(
            self.number, self.__class__.__name__, self.title, self.user.login)

    def __getattr__(self, name):
        return getattr(self._github_obj, name)

    @property
    def description(self):
        return self._github_obj.body

    @property
    def commits(self):
        return self.get_commits()

    @property
    def html(self):
        return requests.get(self._github_obj.html_url).content

    @property
    def patch(self):
        return requests.get(self._github_obj.patch_url).content.encode('UTF-8')

    @property
    def diff(self):
        return requests.get(self._github_obj.diff_url).content.encode('UTF-8')

    @property
    def tags(self):
        return PullRequestTag.fetch(self.title)

    @tags.setter
    def tags(self, tags):
        """Setting the tags <tags> to the pull request title
        """
        if len(set([t.type for t in tags]).union()) != len(tags):
            raise Exception()  # TODO: Implement multiple tags with the same type exception
        return self._github_obj.edit(
            '{} {}'.format(
                ''.join([t.raw for t in tags]), re.split(
                    config().config.github.pull_request_title_tag.pattern, self.title
                    )[-1].strip()
            )
        )

    def remove_tags(self, *tags):
        return self._github_obj.edit(
            '{} {}'.format(
                ''.join([t.raw for t in tags if t not in self.tags]),
                re.split(config().config.github.pull_request_title_tag.pattern,
                         self.title)[-1].strip()
            ).strip()
        )

    @tags.deleter
    def tags(self):
        return self.remove_tags(self.tags)

    @property
    def reviews(self):
        return self.get_reviews()

    @property
    def reviewer_requests(self):
        return self.get_reviewer_requests()

    @property
    def all_reviewers(self):
        # Including both existing reviewers and reviewers from reviewer request
        # Including reviewers that not in the pool
        reviewers = []
        for review in self.reviews:
            reviewers.append(ReviewerUser(review.user.login))
        for review_request in self.reviewer_requests:
            reviewer = ReviewerUser(review_request.login)
            if reviewer not in reviewers:
                reviewers.append(reviewer)
        return list(set(reviewers))

    @property
    def reviewers(self):
        reviewers = self.all_reviewers
        # Filtering reviewers that not in the pool and updating the pool
        for reviewer in reviewers:
            if reviewer in self.repo.reviewers_pool.reviewers:
                self.repo.reviewers_pool.update_reviewer_stat(reviewer, self.number)
            else:
                reviewers.remove(reviewer)
        return reviewers

    def create_review(self, commit, body, event=None, comments=None):
        """

        this is workaround until
        https://github.com/PyGithub/PyGithub/pull/662 is merged.

        :calls: `POST /repos/:owner/:repo/pulls/:number/reviews
                <https://developer.github.com/v3/pulls/reviews/>`_
        :param commit: github.Commit.Commit
        :param body: string
        :param event: string
        :param issue_comments: list
        :rtype: :class:`github.PaginatedList.PaginatedList` of
                :class:`github.PullRequestReview.PullRequestReview`
        """
        assert isinstance(body, basestring), body
        assert event is None or isinstance(event, basestring), event
        assert comments is None or isinstance(comments, list), comments
        post_parameters = {'commit_id': commit.sha, 'body': body}
        post_parameters['event'] = 'PENDING' if event is None else event
        if comments is None:
            post_parameters['issue_comments'] = []
        headers, data = self._requester.requestJsonAndCheck(
            "POST",
            self.url + "/reviews",
            input=post_parameters
        )
        self._useAttributes(data)

    def add_reviewers(self, reviewers):
        """Adding the reviewers to the pull request - this is workaround until
        https://github.com/PyGithub/PyGithub/pull/598 is merged.
        :calls: `POST /repos/:owner/:repo/pulls/:number/requested_reviewers
                <https://developer.github.com/v3/pulls/review_requests/>`_
        :param reviewers: (logins) list of strings or User
        """
        status, _, _ = self._github_obj._requester.requestJson(
            "POST",
            self.url + "/requested_reviewers",
            input={'reviewers': [rev.login if isinstance(rev, User) else rev for rev in reviewers]},
            headers={'Accept': 'application/vnd.github.thor-preview+json'}
        )
        return status == 201

    def remove_reviewers(self, reviewers):
        """Removing the reviewers from the pull request - this is workaround until
        https://github.com/PyGithub/PyGithub/pull/598 is merged.
        :calls: `DELETE /repos/:owner/:repo/pulls/:number/requested_reviewers
                <https://developer.github.com/v3/pulls/review_requests/>`_
        :param reviewers: (logins) list of strings
        """
        status, _, _ = self._github_obj._requester.requestJson(
            "DELETE",
            self.url + "/requested_reviewers",
            input={'reviewers': [rev.login if isinstance(rev, User) else rev for rev in reviewers]},
            headers={'Accept': 'application/vnd.github.thor-preview+json'}
        )
        return status == 200

    @property
    def age(self):
        now = datetime.now()
        return now - self._github_obj.created_at

    @property
    def review_comments(self):
        comments = [c for c in self._github_obj.get_review_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def review_comment_threads(self):
        return ReviewCommentThread.fetch_threads(self)

    @property
    def last_review_comment(self):
        review_comments = self.review_comments
        if review_comments:
            return max(review_comments, key=lambda item: item.updated_at)

    @property
    def issue_comments(self):
        comments = [c for c in self._github_obj.get_issue_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def test_results(self):
        tests = json.loads(requests.get(self._github_obj.raw_data['statuses_url']).content)
        out = {}
        for test in tests:
            out[test['context']] = test['description']
        return out

    @property
    def owner(self):
        return ContributorUser(self._github_obj.user)

    @property
    def last_code_update(self):
        return dateparser.parse(list(self._github_obj.get_commits()).pop().last_modified)

    @property
    def last_update(self):
        return self._github_obj.updated_at

    @property
    def json(self):
        """Get the object data as dictionary"""
        lst_cmnt = self.last_review_comment
        age_total_seconds = int(self.age.total_seconds())
        days_ago = age_total_seconds / 86400
        hours_ago = (age_total_seconds - days_ago * 86400) / 3600
        out = {
            'repo': self.repo.name,
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
