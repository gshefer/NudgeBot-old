# NudgeBot

NudgeBot is a Pull Requests review and repository tracking bot which collects statistics and performs actions in a Github repository.

It's called "NudgeBot" since originally it used to "nudge" reviewers to review pull requests after some period without comment.

_______________________

__Note__: :hand: _This project is still not a generic framework (not yet). Currently it's under development and in use and tested internally._ :hand:
_______________________

## Functionality:
- Performs actions in Pull Requests, i.e. add reviewers, post comment, etc.
- Collects Pull Requests statistics and repository statistics.
- Sends reports to the repository maintainers.
- Provides a live dashboard which presents the current statistics/status of the review process. E.g.

  ![alt text](https://raw.githubusercontent.com/gshefer/NudgeBot-old/master/doc/reviewers_pool_table.png)
  ![alt text](https://raw.githubusercontent.com/gshefer/NudgeBot-old/master/doc/pull_request_statistics_table.png)

## Design:
### Base components:

- [flow tree](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/flow.py), A tree that describes the action to perform for each case in a Pull Request. This flow tree consists of:
  - [Case](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/actions/__init__.py) - Describes a situation in the Pull Request, a "Case".
  - [Action](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/cases/__init__.py) - Describes an action to perform in these situations/cases.
- [Pull request statistics](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/github/pull_request_statistics.py) Contains various statistics of a Pull Request.
- [Reviewers pool](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/github/reviewers_pool.py) a pool that containing the reviewers of the repository, including number of PRs per reviewer, this object used to decide which reviewer to set per pull request.
- [The bot](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/__init__.py) The NudgeBot that handles the events, processes the flow and performs actions.
- [Reports](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/reports) Provides the ability to easily produce, trigger and report about the repository.
- [Server](https://github.com/gshefer/NudgeBot/tree/master/nudgebot/server) The server side.
- [Config](https://github.com/gshefer/NudgeBot/tree/master/config) Includes the configuration file and credentials.

## Future plans:
- Change the server to use Django instead of flask.
- Extend the functionality to include more statistics about the repository.
### Notes:
- More documentation will be released later.
