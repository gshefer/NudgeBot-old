# -*- coding: utf-8 -*-
import json
import re

from cached_property import cached_property
import dateparser
import requests

from .users import User, ContributorUser, ReviewerUser
from config import config
from common import Age


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
    def comments(self):
        return sorted(self._comments, key=lambda c: c.created_at)

    @property
    def first_comment(self):
        return self.comments[0]

    @property
    def last_comment(self):
        return self.comments[-1]

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


class PullRequestTitleTag(object):
    """Represents Pull Request title tag.
    e.g. [RFR], [WIP], ...
    """

    @classmethod
    def fetch(cls, title):
        """PullRequestTitleTag Factory - fetching title_tags from title.
        Args:
            * title (str): the Pull request title.
        Returns: list of PullRequestTitleTag
        """
        assert isinstance(title, basestring)
        detected_tags = []
        tag_names = re.findall(config().config.github.pull_request_title_tag.pattern, title)
        for tag_name in tag_names:
            tag_name = tag_name.upper()
            detected_tags.append(cls(tag_name.upper()))
        return detected_tags

    def __init__(self, tag):
        self._tag = (tag.name if isinstance(tag, self.__class__)
                     else tag)

    def __eq__(self, other):
        return self._tag == getattr(other, '_tag', None)

    def __repr__(self, *args, **kwargs):
        return '<{} name="{}">'.format(
            self.__class__.__name__, self.name)

    @property
    def name(self):
        return self._tag

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
        return self._github_obj.body or ''

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
    def title_tags(self):
        return PullRequestTitleTag.fetch(self.title)

    @title_tags.setter
    def title_tags(self, title_tags):
        """Setting the title_tags <title_tags> to the pull request title
        """
        if isinstance(title_tags, basestring):
            title_tags = [title_tags]
        title_tags = [PullRequestTitleTag(tag) for tag in title_tags]
        return self._github_obj.edit(
            '{} {}'.format(
                ''.join([t.raw for t in title_tags]), re.split(
                    config().config.github.pull_request_title_tag.pattern, self.title
                    )[-1].strip()
            )
        )

    def remove_title_tags(self, *title_tags):
        return self._github_obj.edit(
            '{} {}'.format(
                ''.join([t.raw for t in title_tags if t not in self.title_tags]),
                re.split(config().config.github.pull_request_title_tag.pattern,
                         self.title)[-1].strip()
            ).strip()
        )

    @title_tags.deleter
    def title_tags(self):
        return self.remove_title_tags(self.title_tags)

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
                self.repo.reviewers_pool.attach_pr_to_reviewer(reviewer, self.number)
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
        return Age(self._github_obj.created_at)

    @property
    def review_comments(self):
        comments = [c for c in self._github_obj.get_review_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def review_comment_threads(self):
        return ReviewCommentThread.fetch_threads(self)

    @property
    def issue_comments(self):
        comments = [c for c in self._github_obj.get_issue_comments()]
        comments.sort(key=lambda c: c.updated_at)
        return comments

    @property
    def test_results(self):
        auth = (config().credentials.github.username, config().credentials.github.password)
        tests = json.loads(requests.get(self._github_obj.raw_data['statuses_url'], auth=auth).content)
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
    def last_update_age(self):
        return Age(self.last_update)

    @property
    def last_code_update_age(self):
        return Age(self.last_code_update)
