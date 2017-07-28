#!/usr/bin/python
# coding: utf-8

"""
A jabber bot to order a baguette
"""

import HTMLParser
import argparse
import datetime
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText

import requests
import schedule
import xmpp
from bs4 import BeautifulSoup
from jabberbot import JabberBot, botcmd
from pymongo import MongoClient

# Replace NS_DELAY variable by good one
xmpp.NS_DELAY = 'urn:xmpp:delay'


class BaguetteJabberBot(JabberBot):
    """Rennes Baguette bot"""

    def __init__(self, *args, **kwargs):
        """ Initialize variables. """
        self.orders = []
        self.room = None
        self.fromm = None
        self.mail_to = None
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
        schedule.every().monday.at("09:00").do(self.ask_baguette)
        schedule.every().monday.at("09:30").do(self.sendmail)
        schedule.every().thursday.at("09:00").do(self.ask_baguette)
        schedule.every().thursday.at("09:30").do(self.sendmail)
        # Debug schedules
        # schedule.every(10).seconds.do(self.ask_baguette)
        # schedule.every(20).seconds.do(self.sendmail)

    def connect_mongo(self, mongoUser, mongoPassword, mongoUrl):
        # Connect to mongo
        connectString = 'mongodb://' + mongoUser + ':' + mongoPassword + '@' + mongoUrl
        mongoClient = MongoClient(connectString)
        return mongoClient.boulanger

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

    def sendmail(self):
        """ Send email """

        if self.orders:
            msg = MIMEText(
                "Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?"
                "\n\nDemandeurs :\n{}".format(
                    len(self.orders), '\n'.join(self.orders)))
            msg['Subject'] = self.subject
            msg['From'] = self.fromm
            msg['To'] = self.mail_to

            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(self.fromm, [self.mail_to], msg.as_string())
            smtp.quit()

            self.send(text="J'ai envoye la commande a Marie ! cc {}".format(" ".join(self.orders)),
                      user=self.room, message_type="groupchat")

            self.orders = []
        else:
            self.send(text="Pas de commande aujourd'hui !",
                      user=self.room,
                      message_type="groupchat")

    def ask_baguette(self):
        """ Demande aux gens s'ils veulent une baguette """
        self.send(text="Coucou tout le monde! Voulez vous une baguette {} ?".format(self.highlight),
                  user=self.room,
                  message_type="groupchat")

    @botcmd
    def oui(self, mess, args):
        """ Commander une baguette """
        user = mess.getFrom().getResource()
        if user not in self.orders:
            self.orders.append(user)

        self.send_simple_reply(mess, "OK!")

    @botcmd
    def non(self, mess, args):
        """ Annuler la commande d'une baguette """
        user = mess.getFrom().getResource()
        if user in self.orders:
            self.orders.remove(user)

        self.send_simple_reply(mess, "OK!")

    @botcmd
    def list(self, mess, args):
        """ Liste les gens qui veulent une baguette """

        self.send_simple_reply(mess, 'Liste des gens qui veulent une baguette: {}'.format(
            ' '.join(self.orders)))

    @botcmd
    def previens(self, mess, args):
        """ Pour s'ajouter dans la highlight """

        user = mess.getFrom().getResource()
        if user not in self.highlight:
            self.highlight.append(user)

        self.send_simple_reply(mess, 'Ok, je te previendrai avant la prochaine commande de pain.')

    @botcmd
    def osef(self, mess, args):
        """ Pour s\'enlever de la highlight """

        user = mess.getFrom().getResource()
        if user in self.highlight:
            self.highlight.remove(user)

        self.send_simple_reply(mess, 'Ok, va te faire voir')

    @botcmd
    def list_highlight(self, mess, args):
        """ Liste les gens qui veulent etre prevenus de la prochaine commande """
        content = 'Liste des gens qui veulent etre prevenus de la prochaine commande: {}'.format(
            ' '.join(self.highlight))
        self.send_simple_reply(mess, content)

    @botcmd
    def ping(self, mess, args):
        """ Tu veux jouer ? """
        self.send_simple_reply(mess, 'pong')

    @botcmd
    def fact(self, mess, args):
        """ Chuck Norris Facts """
        # Retrieve a fact
        req = requests.get('http://www.chucknorrisfacts.fr/api/get?data=tri:alea;nb:1')
        pars = HTMLParser.HTMLParser()
        if req.status_code == 200:
            fact = req.json()
            self.send_simple_reply(mess, pars.unescape(fact[0]['fact']))
        else:
            self.send_simple_reply(mess, 'Chuck Norris est malade...')

    @botcmd
    def gif(self, mess, args):
        """ Random GIF """
        # Retrieve a gif
        base_url = "http://api.giphy.com/v1/gifs/random"
        api_params = {'api_key': 'dc6zaTOxFJmzC'}

        if args:
            api_params['tag'] = args
        req = requests.get(base_url, params=api_params)
        pars = HTMLParser.HTMLParser()
        if req.status_code == 200:
            fact = req.json()
            self.send_simple_reply(mess, pars.unescape(fact['data']['image_original_url']))
        else:
            self.send_simple_reply(mess, 'Giphy est malade...')

    @botcmd
    def eaty(self, mess, args):
        """ Retourne le menu de Eaty """
        # Retrieve menu
        req = requests.get('http://www.eatyfr.wordpress.com')
        if req.status_code == 200:
            menus = []
            soup = BeautifulSoup(req.text, "html.parser")
            for i in soup.find('div', attrs={'class': 'entry-content'}).findAll("h3")[1:]:
                menu = i.text.strip()
                if not menu.startswith(u'°') and menu != '':
                    menus.append(menu.encode("utf-8"))
            self.send_simple_reply(mess,
                                   'Voici les menus Eaty du jour:\n{}'.format('\n'.join(menus)))
        else:
            self.send_simple_reply(mess, 'Eaty est malade...')

    @botcmd
    def insulte(self, mess, args):
        ''' Insulte quelqu'un '''
        # Lire une insulte
        collection = self.mongoDb.insultes
        elt = collection.aggregate([{'$sample': {'size': 1}}])
        insulte = list(elt)[0]['text']

        # Qui instulter?
        if args and 'Boulanger' not in args:
            self.send_simple_reply(mess, u'{} {}'.format(
                insulte,
                args,
            ))
        else:
            self.send_simple_reply(mess, u'{} {}'.format(
                insulte,
                mess.getFrom().getResource(),
            ))

    @botcmd
    def star(self, mess, args):
        """ Retourne le passage des bus
        Boulanger star [line_code]
        """
        api_params = {
            'dataset': 'tco-bus-circulation-passages-tr',
            'geofilter.distance': '48.128336,-1.625569,500',
            'sort': '-depart',
            'rows': 15,
            'timezone': 'Europe/Paris'
        }
        base_url = 'https://data.explore.star.fr/api/records/1.0/search/'
        splitted_args = args.split()
        if splitted_args and splitted_args[0]:
            api_params['q'] = 'nomcourtligne=%s' % splitted_args[0]
        req = requests.get(base_url, params=api_params, verify=False)
        if req.status_code == 200:
            bus = []
            for record in req.json().get('records', []):
                stop = record['fields']['nomarret']
                line = record['fields']['nomcourtligne']
                destination = record['fields']['destination']
                passing_time = record['fields']['depart']
                # Ugly but working
                parsed_date = datetime.datetime.strptime(passing_time[:-6], "%Y-%m-%dT%H:%M:%S")
                passing_time = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                bus.append('[%s] %s -> %s - [%s]' % (line, stop, destination, passing_time))
            if bus:
                self.send_simple_reply(mess, u'Voici les prochains bus:\n{}'.format('\n'.join(bus)))
            else:
                self.send_simple_reply(mess, "Il n'y a pas de bus prochainement")
        else:
            self.send_simple_reply(mess, 'star est malade...')

    @botcmd
    def piment(self, mess, args):
        """Retourne le plat du jour au piment rouge"""
        now = datetime.datetime.now()

        description = {
            u"BA MI": u"Nouilles de blé, crevettes marinées, raviolis frits, légumes, crudité, sauce sucrée",
            u"Soupe raviolis": u"Nouilles chinoises, raviolis aux crevettes, poulet, herbes aromatiques, soja",
            u"Bo Bun": u"Vermicelles de riz, boeuf woké au curry, cacahuètes concassées, nems, crudités",
            u"Pad Thai": u"Pâtes de riz, poulet, tofu, cacahuètes concassées, soja, ciboulette, sauce caramélisée",
            u"Ragoût vietnamien": u"Pâtes de riz, assortiment de boeuf, herbes aromatiques, bouillon de boeuf"}

        menu = {
            0: [u'BA MI'],
            1: [u'Soupe raviolis'],
            2: [u'Bo Bun'],
            3: [u'Bo Bun'],
            4: [u'Pad Thai', u'Ragoût vietnamien']}

        if now.weekday() > 4:
            self.send_simple_reply(mess, u"Eh oh... J'suis en week end moi reviens lundi")
        else:
            self.send_simple_reply(mess, u"Aujourd'hui le menu de piment rouge est \n%s" % '\n'.join(
                [u'%s => %s' % (ele, description[ele]) for ele in menu[now.weekday()]]))

    @botcmd
    def kaamelott(self, mess, args):
        """Kaamelott"""
        base_url = 'http://kaamelott.underfloor.io/quote/rand'
        req = requests.get(base_url)
        if req.status_code == 200:
            self.send_simple_reply(mess, u'%s: "%s"' % (req.json().get('character', 'Perceval'), req.json().get('quote', "C'est pas faux")))
        else:
            self.send_simple_reply(mess, "J'ai été pas mal malade")


def read_password(username):
    """Read password from $HOME/.p or environment variable"""
    if 'BOT_PASSWORD' in os.environ:
        return os.environ['BOT_PASSWORD']
    with open(os.environ['HOME'] + "/.p", "r+") as current_file:
        for line in current_file.readlines():
            current_tuple = line.split(":")
            if current_tuple[0] == username:
                return current_tuple[1].rstrip()
    print 'No password found'
    return ''


def read_mongo_password():
    """Read password from environment variable"""
    if 'MONGO_PASSWORD' in os.environ:
        return os.environ['MONGO_PASSWORD']
    else:
        return ''


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
                        help="Nickname to highlight when asking questions. Space separated. "
                             "Default is arnaud.morin",
                        default="arnaud.morin")
    parser.add_argument("--fromm",
                        help="Mail address to send from")
    parser.add_argument("--to",
                        help="Mail address to send to")
    parser.add_argument("--subject",
                        help="Subject of mail. Default is Commande de baguette",
                        default="Commande de baguette")
    parser.add_argument("--mongoUser",
                        help="Mongo db user",
                        default="boulanger")
    parser.add_argument("--mongoUrl",
                        help="Mongo db user",
                        default="ds125183.mlab.com:25183/boulanger")
    return parser.parse_args()


def main():
    """Connect to the server and run the bot forever"""
    main_args = parse_args()
    password = read_password(main_args.username.replace("@jabber.ovh.net", ""))
    bot = BaguetteJabberBot(main_args.username, password)
    bot.room = main_args.room
    bot.fromm = main_args.fromm
    bot.mail_to = main_args.to
    bot.subject = main_args.subject
    bot.nick = main_args.nick
    bot.mongoDb = bot.connect_mongo(main_args.mongoUser, read_mongo_password(), main_args.mongoUrl)
    bot.highlight = main_args.highlight.split(' ')
    # create a regex to check if a message is a direct message
    bot.direct_message_re = re.compile(r'^%s?[^\w]?' % main_args.nick)
    try:
        bot.muc_join_room(main_args.room, main_args.nick)
    except AttributeError:
        # Connection error is check after
        pass
    bot.serve_forever()


if __name__ == '__main__':
    main()
