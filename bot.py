#!/usr/bin/python
# coding: utf-8

"""
A jabber bot to order a baguette
"""

import os
import argparse
import re
import logging
import xmpp
import smtplib
import schedule
import requests
import HTMLParser
import random
import datetime
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from jabberbot import JabberBot, botcmd

# Replace NS_DELAY variable by good one
xmpp.NS_DELAY = 'urn:xmpp:delay'

INJURES = [
    "T'es juste un esti de fuck all",
    "Tu pues du bout du bat",
    "Mange de la merde gros sal",
    "Câlice de chien sale",
    "Mange un char de marde ",
    "Tarbanak de crosseur à marde",
    "Sti que t'es cave",
    "En tout cas toi t'es pas une 100 Watt",
]


class BaguetteJabberBot(JabberBot):

    def __init__(self, *args, **kwargs):
        ''' Initialize variables. '''
        self.orders = []
        self.room = None
        self.fromm = None
        self.to = None
        self.subject = None
        self.nick = None
        self.highlight = []

        try:
            del kwargs['room']
            del kwargs['fromm']
            del kwargs['to']
            del kwargs['subject']
            del kwargs['nick']
            del kwargs['highlight']
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
        schedule.every().monday.at("09:00").do(self.askBaguette)
        schedule.every().monday.at("09:30").do(self.sendmail)
        schedule.every().thursday.at("09:00").do(self.askBaguette)
        schedule.every().thursday.at("09:30").do(self.sendmail)
        # Debug schedules
        # schedule.every(10).seconds.do(self.askBaguette)
        # schedule.every(20).seconds.do(self.sendmail)

    def callback_message(self, conn, mess):
        ''' Changes the behaviour of the JabberBot in order to allow
        it to answer direct messages. This is used often when it is
        connected in MUCs (multiple users chatroom). '''

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

    def sendmail(self):
        ''' Send email '''

        if self.orders:
            msg = MIMEText("Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?\n\nDemandeurs :\n{}".format(
                           len(self.orders),
                           '\n'.join(self.orders),
                           ))
            msg['Subject'] = self.subject
            msg['From'] = self.fromm
            msg['To'] = self.to

            s = smtplib.SMTP('localhost')
            s.sendmail(self.fromm, [self.to], msg.as_string())
            s.quit()

            self.send(text="J'ai envoye la commande a Marie ! cc {}".format(
                " ".join(self.orders)),
                user=self.room,
                message_type="groupchat")

            self.orders = []
        else:
            self.send(text="Pas de commande aujourd'hui !",
                      user=self.room,
                      message_type="groupchat")

    def askBaguette(self):
        ''' Demande aux gens s'ils veulent une baguette '''
        self.send(text="Coucou tout le monde! Voulez vous une baguette {} ?".format(self.highlight), user=self.room, message_type="groupchat")

    @botcmd
    def oui(self, mess, args):
        ''' Commander une baguette '''
        user = mess.getFrom().getResource()
        if user not in self.orders:
            self.orders.append(user)

        self.send_simple_reply(mess, "OK!")

    @botcmd
    def non(self, mess, args):
        ''' Annuler la commande d'une baguette '''
        user = mess.getFrom().getResource()
        if user in self.orders:
            self.orders.remove(user)

        self.send_simple_reply(mess, "OK!")

    @botcmd
    def list(self, mess, args):
        ''' Liste les gens qui veulent une baguette '''

        self.send_simple_reply(mess, 'Liste des gens qui veulent une baguette: {}'.format(' '.join(self.orders)))

    @botcmd
    def previens(self, mess, args):
        ''' Pour s\'ajouter dans la highlight '''

        user = mess.getFrom().getResource()
        if user not in self.highlight:
            self.highlight.append(user)

        self.send_simple_reply(mess, 'Ok, je te previendrai avant la prochaine commande de pain.')

    @botcmd
    def osef(self, mess, args):
        ''' Pour s\'enlever de la highlight '''

        user = mess.getFrom().getResource()
        if user in self.highlight:
            self.highlight.remove(user)

        self.send_simple_reply(mess, 'Ok, va te faire voir')

    @botcmd
    def list_highlight(self, mess, args):
        ''' Liste les gens qui veulent etre prevenus de la prochaine commande '''

        self.send_simple_reply(mess, 'Liste des gens qui veulent etre prevenus de la prochaine commande: {}'.format(' '.join(self.highlight)))

    @botcmd
    def ping(self, mess, args):
        ''' Tu veux jouer ? '''
        self.send_simple_reply(mess, 'pong')

    @botcmd
    def fact(self, mess, args):
        ''' Chuck Norris Facts '''
        # Retrieve a fact
        r = requests.get('http://www.chucknorrisfacts.fr/api/get?data=tri:alea;nb:1')
        pars = HTMLParser.HTMLParser()
        if r.status_code == 200:
            fact = r.json()
            self.send_simple_reply(mess, pars.unescape(fact[0]['fact']))
        else:
            self.send_simple_reply(mess, 'Chuck Norris est malade...')

    @botcmd
    def gif(self, mess, args):
        ''' Random GIF '''
        # Retrieve a gif
        base_url = "http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC"
        splitted_args = args.split()
        if splitted_args and splitted_args[0]:
            base_url += "&tag={}".format(splitted_args[0])
        r = requests.get(base_url)
        pars = HTMLParser.HTMLParser()
        if r.status_code == 200:
            fact = r.json()
            self.send_simple_reply(mess, pars.unescape(fact['data']['image_original_url']))
        else:
            self.send_simple_reply(mess, 'Giphy est malade...')

    @botcmd
    def eaty(self, mess, args):
        ''' Retourne le menu de Eaty '''
        # Retrieve menu
        r = requests.get('http://www.eatyfr.wordpress.com')
        if r.status_code == 200:
            menus = []
            soup = BeautifulSoup(r.text, "html.parser")
            for i in soup.find('div', attrs={'class': 'entry-content'}).findAll("h3")[1:]:
                menu = i.text.strip()
                if not menu.startswith(u'°') and menu != '':
                    menus.append(menu.encode("utf-8"))
            self.send_simple_reply(mess, 'Voici les menus Eaty du jour:\n{}'.format('\n'.join(menus)))
        else:
            self.send_simple_reply(mess, 'Eaty est malade...')

    @botcmd
    def insulte(self, mess, args):
        ''' Insulte quelqu'un '''
        # Qui instulter?
        if args:
            self.send_simple_reply(mess, '{} {}'.format(
                random.choice(INJURES),
                args,
            ))
        else:
            self.send_simple_reply(mess, '{} {}'.format(
                random.choice(INJURES),
                mess.getFrom().getResource(),
            ))

    @botcmd
    def star(self, mess, args):
        ''' Retourne le passage des bus '''
        base_url = 'https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-circulation-passages-tr&geofilter.distance=48.128336%2C+-1.625569%2C500&sort=-depart&rows=15&&timezone=Europe%2FParis'
        splitted_args = args.split()
        if splitted_args and splitted_args[0]:
            base_url += '&q=nomcourtligne%%3D%s' % splitted_args[0]
        r = requests.get(base_url, verify=False)
        if r.status_code == 200:
            bus = []
            for record in r.json().get('records', []):
                stop = record['fields']['nomarret']
                line = record['fields']['nomcourtligne']
                destination = record['fields']['destination']
                passing_time = record['fields']['depart']
                # Ugly but working
                parsed_date = datetime.datetime.strptime(passing_time[:-6], "%Y-%m-%dT%H:%M:%S")
                passing_time = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                bus.append('[%s] %s -> %s - [%s]' % (line, stop, destination, passing_time))
            if len(bus):
                self.send_simple_reply(mess, u'Voici les prochains bus:\n{}'.format('\n'.join(bus)))
            else:
                self.send_simple_reply(mess, "Il n'y a pas de bus prochainement")
        else:
            self.send_simple_reply(mess, 'star est malade...')


def read_password(username):
    """Read password from $HOME/.p or environment variable"""
    if 'BOT_PASSWORD' in os.environ:
        return os.environ['BOT_PASSWORD']
    else:
        f = open(os.environ['HOME'] + "/.p", "r+")
        for line in f.readlines():
            tuple = line.split(":")
            if tuple[0] == username:
                password = tuple[1].rstrip()
        f.close()
        return password


def parse_args():
    """
    Parse command line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--username",
                        help="Username")
    parser.add_argument("--room",
                        help="Room to join. Default is pcr@conference.jabber.ovh.net",
                        default="pcr@conference.jabber.ovh.net")
    parser.add_argument("--nick",
                        help="Nick name to show. Default is Boulanger",
                        default="Boulanger")
    parser.add_argument("--highlight",
                        help="Nickname to highlight when asking questions. Space separated. Default is arnaud.morin",
                        default="arnaud.morin")
    parser.add_argument("--fromm",
                        help="Mail address to send from")
    parser.add_argument("--to",
                        help="Mail address to send to")
    parser.add_argument("--subject",
                        help="Subject of mail. Default is Commande de baguette",
                        default="Commande de baguette")
    return parser.parse_args()


if __name__ == '__main__':
    "Connect to the server and run the bot forever"
    args = parse_args()
    password = read_password(args.username.replace("@jabber.ovh.net", ""))
    bot = BaguetteJabberBot(args.username, password)
    bot.room = args.room
    bot.fromm = args.fromm
    bot.to = args.to
    bot.subject = args.subject
    bot.nick = args.nick
    bot.highlight = args.highlight.split(' ')
    # create a regex to check if a message is a direct message
    bot.direct_message_re = re.compile('^%s?[^\w]?' % args.nick)
    try:
        bot.muc_join_room(args.room, args.nick)
    except AttributeError as e:
        # Connection error is check after
        pass
    bot.serve_forever()
