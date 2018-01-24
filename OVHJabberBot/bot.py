#!/usr/bin/python
# coding: utf-8

"""
A jabber bot to order a baguette
"""


import logging
import smtplib
from email.mime.text import MIMEText

import schedule
from jabberbot import JabberBot, botcmd
import xmpp

from db.order import Order
from db.notif import Notif

# Replace NS_DELAY variable by good one
xmpp.NS_DELAY = 'urn:xmpp:delay'

class SingletonType(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance

class BaguetteJabberBot(JabberBot):
    """Rennes Baguette bot"""
    __metaclass__ = SingletonType

    def __init__(self, *args, **kwargs):

        """ Initialize variables. """
        self.room = None
        self.fromm = None
        self.mail_to = None
        self.subject = None
        self.nick = None
        self.first_round = True

        try:
            del kwargs['room']
            del kwargs['fromm']
            del kwargs['to']
            del kwargs['subject']
            del kwargs['nick']
        except KeyError:
            pass

        # answer only direct messages or not?
        self.only_direct = kwargs.get('only_direct', True)
        try:
            del kwargs['only_direct']
        except KeyError:
            pass

        # initialize jabberbot
        super(BaguetteJabberBot, self).__init__(*args, **kwargs)

        # create console handler
        chandler = logging.StreamHandler()
        # create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # add formatter to handler
        chandler.setFormatter(formatter)
        # add handler to logger
        self.log.addHandler(chandler)
        # set level to INFO
        self.log.setLevel(logging.INFO)

        # Add some schedules
        schedule.every().monday.at("09:00").do(self.ask_baguette)
        schedule.every().monday.at("09:15").do(self.ask_baguette)
        schedule.every().monday.at("09:30").do(self.ask_baguette)
        schedule.every().monday.at("09:45").do(self.sendmail)
        schedule.every().thursday.at("09:00").do(self.ask_baguette)
        schedule.every().thursday.at("09:15").do(self.ask_baguette)
        schedule.every().thursday.at("09:30").do(self.ask_baguette)
        schedule.every().thursday.at("09:45").do(self.sendmail)

    def callback_message(self, conn, mess):
        """ Changes the behaviour of the JabberBot in order to allow
        it to answer direct messages. This is used often when it is
        connected in MUCs (multiple users chatroom). """

        message = mess.getBody()
        if not message:
            return

        if self.direct_message_re.match(message):
            mess.setBody(' '.join(message.split(' ', 1)[1:]))
            return super(BaguetteJabberBot, self).callback_message(conn, mess)
        elif not self.only_direct:
            return super(BaguetteJabberBot, self).callback_message(conn, mess)

    def idle_proc(self):
        """This function will be called in the main loop."""
        schedule.run_pending()
        self._idle_ping()

    def register_command(self, name, command):
        self.commands[name] = command
        self.log.info("Loaded command {}".format(name))

    def sendmail(self):
        """ Send email """
        orders = Order.objects()

        if orders:
            msg = MIMEText(
                "Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?"
                "\n\nDemandeurs :\n{}".format(
                    len(orders), '\n'.join([o.name for o in orders])))
            msg['Subject'] = self.subject
            msg['From'] = self.fromm
            msg['To'] = self.mail_to

            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(self.fromm, [self.mail_to], msg.as_string())
            smtp.quit()

            self.send(text="J'ai envoye la commande a Marie ! cc {}".format(" ".join([o.name for o in orders])),
                      user=self.room, message_type="groupchat")

            for user in orders:
                self.delete_user_orders(user)
        else:
            self.send(text="Pas de commande aujourd'hui !",
                      user=self.room,
                      message_type="groupchat")

    def ask_baguette(self):
        """ Demande aux gens s'ils veulent une baguette """
        orders = Order.objects()
        notifs = Notif.objects()

        results = [user.name for user in notifs if user not in [order.name for order in orders]]

        self.send(text="Coucou tout le monde! Voulez vous une baguette {} ?".format(
            ' '.join(map(str, results))),
            user=self.room,
            message_type="groupchat")
