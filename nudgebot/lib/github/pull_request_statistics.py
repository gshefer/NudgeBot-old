from datetime import datetime

from cached_property import cached_property

from nudgebot.lib.github.users import ReviewerUser
from nudgebot.lib.statistics import Statistics, stat_property


class PullRequestStatistics(Statistics):

    def __init__(self, pull_request):
        self._pull_request = pull_request

    @cached_property
    def pull_request(self):
        return self._pull_request

    @stat_property
    def title(self):
        return self._pull_request.title

    @stat_property
    def owner(self):
        return self._pull_request.owner

    @stat_property
    def description(self):
        return self._pull_request.description

    @stat_property
    def age(self):
        return self._pull_request.created_at

    @stat_property
    def number(self):
        return self._pull_request.number

    @stat_property
    def repo(self):
        return self._pull_request.repo

    @stat_property
    def org(self):
        return self.repo().organization or self.repo().owner

    @stat_property
    def commits(self):
        return self._pull_request.commits

    @stat_property
    def issue_comments(self):
        return self._pull_request.issue_comments

    @stat_property
    def review_comments(self):
        return self._pull_request.review_comments

    @stat_property
    def test_results(self):
        return self._pull_request.test_results

    @stat_property
    def last_code_update(self):
        return self._pull_request.last_code_update

    @stat_property
    def last_update(self):
        return self._pull_request.last_update

    @stat_property
    def time_since_last_update(self):
        return datetime.now() - self.last_update()

    @stat_property
    def title_tags(self):
        return self._pull_request.title_tags

    @stat_property
    def reviews(self):
        return self._pull_request.reviews

    @stat_property
    def reviewer_requests(self):
        return self.pull_request.get_reviewer_requests()

    @stat_property
    def reviewers(self):
        return self._pull_request.reviewers

    @stat_property
    def review_states_by_user(self):
        review_states = {}
        for review in self.reviews():
            review_states[ReviewerUser(review.user.login)] = review.state
        return review_states

    @stat_property
    def last_review_comment(self):
        review_comments = self.review_comments()
        if review_comments:
            return max(review_comments, key=lambda item: (item.updated_at or item.created_at))

    @stat_property
    def review_comment_reaction_statuses(self):
        statuses = []
        review_states = self.review_states_by_user()
        review_comment_threads = self.pull_request.review_comment_threads
        for thread in review_comment_threads:
            if not thread.outdated:
                last_comment = thread.last_comment
                reviewer = ReviewerUser(thread.first_comment.user.login)
                is_require_changes = review_states.get(reviewer) == 'CHANGES_REQUESTED'
                if is_require_changes:
                    age_seconds = (datetime.now() - last_comment.created_at).total_seconds()
                    statuses.append({
                        'reviewer': reviewer,
                        'contributor': self.owner(),
                        'last_comment': last_comment,
                        'age_seconds': age_seconds
                    })
        return statuses

    @stat_property
    def total_review_comments(self):
        return len(self.pull_request.review_comments)

    @stat_property
    def total_review_comment_threads(self):
        return len(self.pull_request.review_comment_threads)

    def get_json(self):
        """Get the object data as dictionary"""
        last_review_comment = self.last_review_comment()
        data = {
            'number': self.number(),
            'title': self.title(),
            'owner': self.owner().login,
            'description': self.description(),
            'age': self.age(),
            'organization': getattr(self.org(), 'login', self.org().name),
            'repository': self.repo().name,
            'last_update': self.last_update(),
            'test_results': self.test_results(),
            'title_tags': [tt.name for tt in self.title_tags()],
            'reviewers': [reviewer.login for reviewer in self.reviewers()],
            'review_states_by_user': {user.login: state for user, state in self.review_states_by_user().items()},
            'total_review_comments': self.total_review_comments(),
            'total_review_comment_threads': self.total_review_comment_threads(),
            'last_review_comment': {'login': '', 'body': '', 'updated_at': ''}
        }
        if last_review_comment:
            data['last_review_comment'] = {
                'login': last_review_comment.user.login,
                'body': last_review_comment.body,
                'updated_at': last_review_comment.updated_at
            }
        return data
