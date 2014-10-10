import os

from lymph import monkey
monkey._export()

import lymph

from machine import Poll
from machine import Option


class VoteCountingService(lymph.Interface):

    service_type='counter'
    logging_path = None

    def __init__(self, container):
        super(VoteCountingService, self).__init__(container)
        self.polls = []


    def apply_config(self, config):
        self.logging_path = os.path.join(
            config.get('logging_path', None), self.service_type + ".log"
        )

    def on_start(self):
        super(VoteCountingService, self).on_start()
        self._logging_fh = open(self.logging_path, "aw")
        self._logging_fh.write("STARTING VOTING COUNTING\n")
        self._logging_fh.flush()

    def on_stop(self):
        self._logging_fh.write("STOPPING VOTING COUNTING\n")
        self._logging_fh.close()
        super(VoteCountingService, self).on_stop()

    @lymph.event('poll_created')
    def on_poll_created(self, event):
        data = event.body
        poll = Poll(data['question'])
        self.polls.append(poll)
        self._logging_fh.write('POLL REGISTERED: {0}\n'.format(poll.text))
        self._logging_fh.flush()

    @lymph.event('option_created')
    def on_option_created(self, event):
        data = event.body
        poll = self.polls[data['poll_id']]
        option = Option(data['text'])
        option.count = 0
        poll.add_option(option)
        self._logging_fh.write('OPTION REGISTERED: {0} - {1}\n'.format(poll.text, option.text))
        self._logging_fh.flush()

    @lymph.event('voted')
    def on_voted(self, event):
        data = event.body
        poll = self.polls[data['poll_id']] 
        voter_id = data['voter_id']
        vote = data['vote']
        
        option = poll.options[vote]

        try:
            option.count += 1
        except AttributeError:
            option.count = 1


        self._logging_fh.write(
            'VOTE REGISTERED: {0} - {1} - {2} - {3}\n'.format(
                event.source, poll.text, option.text, option.count
             )
        )
        self._logging_fh.flush()

