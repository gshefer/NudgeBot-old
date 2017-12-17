from datetime import datetime

from cached_property import cached_property

from nudgebot.lib.github.users import ReviewerUser
from nudgebot.lib.github.actions import RequestChanges


class PullRequestStatistics(object):

    def __init__(self, pull_request):
        self._pull_request = pull_request

    @cached_property
    def pull_request(self):
        return self._pull_request

    @cached_property
    def title(self):
        return self.pull_request.title

    @cached_property
    def owner(self):
        return self.pull_request.owner

    @cached_property
    def description(self):
        return self._pull_request.description

    @cached_property
    def age(self):
        return self._pull_request.age

    @cached_property
    def number(self):
        return self._pull_request.number

    @cached_property
    def repo(self):
        return self._pull_request.repo

    @cached_property
    def commits(self):
        return self._pull_request.commits

    @cached_property
    def issue_comments(self):
        return self._pull_request.issue_comments

    @cached_property
    def review_comments(self):
        return self._pull_request.review_comments

    @cached_property
    def test_results(self):
        return self._pull_request.test_results

    @cached_property
    def last_code_update(self):
        return self._pull_request.last_code_update

    @cached_property
    def last_update(self):
        return self._pull_request.last_update

    @cached_property
    def title_tags(self):
        return self._pull_request.title_tags

    @cached_property
    def reviews(self):
        return self._pull_request.reviews

    @cached_property
    def reviewer_requests(self):
        return self.pull_request.get_reviewer_requests()

    @cached_property
    def reviewers(self):
        return self._pull_request.reviewers

    @cached_property
    def review_states_by_user(self):
        review_states = {}
        for review in self.reviews:
            review_states[ReviewerUser(review.user.login)] = review.state
        return review_states

    @cached_property
    def last_review_comment(self):
        review_comments = self.review_comments
        if review_comments:
            return max(review_comments, key=lambda item: item.updated_at)

    @cached_property
    def review_comment_reaction_statuses(self):
        statuses = []
        review_states = self.review_states_by_user
        review_comment_threads = self.pull_request.review_comment_threads
        for thread in review_comment_threads:
            if not thread.outdated:
                last_comment = thread.last_comment
                reviewer = ReviewerUser(thread.first_comment.user.login)
                is_require_changes = review_states.get(reviewer) == RequestChanges.STATE
                if is_require_changes:
                    age_seconds = (datetime.now() - last_comment.created_at).total_seconds()
                    statuses.append({
                        'reviewer': reviewer,
                        'contributor': self.owner,
                        'last_comment': last_comment,
                        'age_seconds': age_seconds
                    })
        return statuses

    @property
    def json(self):
        """Get the object data as dictionary"""
        last_review_comment = self.last_review_comment
        age_total_seconds = int(self.age.total_seconds())
        days_ago = age_total_seconds / 86400
        hours_ago = (age_total_seconds - days_ago * 86400) / 3600
        data = {
            'number': self.number,
            'title': self.title,
            'owner': self.owner.login,
            'description': self.description,
            'age': {
                'days': days_ago,
                'hours': hours_ago
            },
            'repository': self.repo.name,
            'last_update': str(self.last_update),
            'test_results': self.test_results,
            'title_tags': [tt.name for tt in self.title_tags],
            'reviewers': [reviewer.login for reviewer in self.reviewers],
            'review_states_by_user': {user.login: state for user, state in self.review_states_by_user.items()},
        }
        if last_review_comment:
            data['last_review_comment'] = {
                'login': last_review_comment.user.login,
                'body': last_review_comment.body,
                'updated_at': last_review_comment.updated_at
            }
        return data
