import os

from lymph import monkey
monkey._export()

import lymph


class Poll(object):
    """
    """

    def __init__(self, text=""):
        self.text = text
        self.options = []

    def add_option(self, option):
        self.options.append(option)
        return len(self.options) - 1

    def set_option(self, id, option):
        self.options[id] = option

    def delete_option(self, id):
        del self.option[id]


class Option(object):
    
    def __init__(self, text=""):
        self.text = text


class VotingMachineService(lymph.Interface):

    service_type = "machine"
    logging_path = None

    def __init__(self, container):
        super(VotingMachineService, self).__init__(container)
        self.polls = []

    def apply_config(self, config):
        self.logging_path = os.path.join(
            config.get('logging_path', None), self.service_type + ".log"
        )

    def on_start(self):
        super(VotingMachineService, self).on_start()
        self._logging_fh = open(self.logging_path, "aw")
        self._logging_fh.write("STARTING VOTING MACHINE\n")
        self._logging_fh.flush()

    def on_stop(self):
        self._logging_fh.write("STOPPING VOTING MACHINE\n")
        self._logging_fh.close()
        super(VotingMachineService, self).on_stop()

    @lymph.rpc()
    def create_poll(self, channel, question=None):
        poll = Poll(text=question)
        self.polls.append(poll)
        id = len(self.polls) - 1
        channel.reply(id)

        event_context = {
            'poll_id': id, 
            'question': question
        }
        self.emit('poll_created', event_context)

    @lymph.rpc()
    def get_polls(self, channel):
        polls = [(_id, poll.text) for _id, poll in enumerate(self.polls)]
        channel.reply(polls)

    @lymph.rpc()
    def get_poll(self, channel, id=None):
        try:
            poll = self.polls[id]
        except IndexError:
            channel.error(type="IndexError", message="Poll with given id not found.")
        else:
            options = [(_id, option.text) for _id, option in enumerate(poll.options)]
            channel.reply(options)

    @lymph.rpc()
    def create_option(self, channel, poll_id=None, option=None):
        try:
            poll = self.polls[poll_id]
        except IndexError:
            channel.error(type="IndexError", message="Poll with given id not found.")
        else:
            option = Option(option)
            option_id = poll.add_option(option)
            channel.reply(option_id)

            event_context = {
                'option_id': option_id, 
                'poll_id': poll_id,
                'text': option.text
            }
            self.emit('option_created', event_context)

    @lymph.rpc()
    def delete_option(self, channel, poll_id=None, option_id=None):
        try:
            poll = self.polls[poll_id]
        except IndexError:
            channel.error(type="IndexError", message="Poll with given id not found.")
        else:
            try:
                del poll.options[option_id]
            except IndexError:
                channel.error(type="IndexError", message="Option with the given id not found")
            else:
                channel.ack()

    @lymph.rpc()
    def vote(self, channel, voter_id=None, poll_id=None, vote=None):
        try:
            poll = self.polls[poll_id]
        except IndexError:
            channel.error(type="IndexError", message="Poll with given id not found.")
        else:
            try:
                option = poll.options[vote]
            except IndexError:
                channel.error(type="IndexError", message="Option with the given id not found")
            else:
                channel.reply(option.text)
                vote_context = {
                    'poll_id': poll_id, 
                    'voter_id': voter_id, 
                    'vote': vote
                }
                self.emit('voted', vote_context)

                log = 'Vote Received: Machine {0} - Voter Id - {1}: {2} - {3}\n'
                self._logging_fh.write(log.format(
                    self.container.identity, 
                    voter_id,
                    poll_id, 
                    option.text
                ))

                self._logging_fh.flush()

