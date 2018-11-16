#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A jabber bot to order a baguette
"""

import logging
import slixmpp

from utils import parse_args
from commands.pain import Pain


class BoulangerBot(slixmpp.ClientXMPP):

    """
    A simple Slixmpp bot that will greets those
    who enter the room, and acknowledge any messages
    that mentions the bot's nickname.
    """

    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.pain = Pain()

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

        # The groupchat_presence event is triggered whenever a
        # presence stanza is received from any chat room, including
        # any presences you send yourself. To limit event handling
        # to a single room, use the events muc::room@server::presence,
        # muc::room@server::got_online, or muc::room@server::got_offline.
        # self.add_event_handler("muc::%s::got_online" % self.room,
        #                       self.muc_online)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room,
                                         self.nick,
                                         # If a room password is needed, use:
                                         # password=the_room_password,
                                         wait=True)

    def muc_message(self, msg):
        """
        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.

        Whenever the bot's nickname is mentioned, respond to
        the message.

        IMPORTANT: Always check that a message is not from yourself,
                   otherwise you will create an infinite loop responding
                   to your own messages.

        This handler will reply to messages that mention
        the bot's nickname.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            # Process message to get command
            processed_message = self.process_message(msg['body'])

            # Execute command to retrieve the result
            # Send the result
            username = msg.get_mucnick()
            if processed_message['command'].lower() == 'oui':
                self.pain.oui(username)
                msg = 'OK'
            elif processed_message['command'].lower() == 'non':
                self.pain.non(username)
                msg = 'OK'
            elif processed_message['command'].lower() == 'liste':
                msg = self.pain.liste_orders()
            else:
                msg = "Je n'ai rien compris"

            self.send_message(
                mto=self.room,
                mbody=msg,
                mtype='groupchat')

    def process_message(self, message):
        """
        Process a message to retrieve the command
        """
        words = message.split(' ', 2)
        if len(words) > 2:
            return {'command': words[1], 'parameters': words[2]}
        elif len(words) > 1:
            return {'command': words[1], 'parameters': ''}
        else:
            return {'command': '', 'parameters': ''}

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.

        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')


if __name__ == '__main__':
    args = parse_args()

    # Setup logging.
    logging.basicConfig(level=logging.ERROR,
                        format='%(levelname)-8s %(message)s')

    # Setup the BoulangerBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = BoulangerBot(args['jid'], args['password'], args['room'], args['nick'])
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
