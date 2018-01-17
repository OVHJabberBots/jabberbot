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
import sys
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
        # Debug schedules
        # schedule.every(10).seconds.do(self.ask_baguette)
        # schedule.every(20).seconds.do(self.sendmail)

    def connect_mongo(self, mongoUser, mongoPassword, mongoUrl):
        # Connect to mongo

        if mongoPassword is not "":
            connectString = 'mongodb://' + mongoUser + ':' + mongoPassword + '@' + mongoUrl
        else:
            connectString = 'mongodb://' + mongoUrl
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
        orders = self.get_users_orders()

        if orders:
            msg = MIMEText(
                "Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?"
                "\n\nDemandeurs :\n{}".format(
                    len(orders), '\n'.join(orders)))
            msg['Subject'] = self.subject
            msg['From'] = self.fromm
            msg['To'] = self.mail_to

            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(self.fromm, [self.mail_to], msg.as_string())
            smtp.quit()

            self.send(text="J'ai envoye la commande a Marie ! cc {}".format(" ".join(orders)),
                      user=self.room, message_type="groupchat")

            for user in orders:
                self.delete_user_orders(user)
        else:
            self.send(text="Pas de commande aujourd'hui !",
                      user=self.room,
                      message_type="groupchat")

    def get_users_notif(self):
        """Recupere les users qui veulent une notification"""
        return [u['name'] for u in list(self.mongoDb.notif.find())]

    def add_user_notif(self, user):
        """Ajoute un user dans la liste des notifs"""
        self.mongoDb.notif.insert({'name': '{}'.format(user)})

    def delete_user_notif(self, user):
        """Supprime un user de la liste des notifs"""
        self.mongoDb.notif.delete_one({'name': '{}'.format(user)})

    def get_users_chase(self):
        """Recupere les users qui veulent se faire harceler"""
        return [u['name'] for u in list(self.mongoDb.chase.find())]

    def add_user_chase(self, user):
        """Ajoute un user dans la liste des harcelements"""
        self.mongoDb.chase.insert({'name': '{}'.format(user)})

    def delete_user_chase(self, user):
        """Supprime un user de la liste des harcelements"""
        self.mongoDb.chase.delete_one({'name': '{}'.format(user)})

    def get_users_orders(self):
        """Recupere les orders en attentes"""
        return [u['name'] for u in list(self.mongoDb.orders.find())]

    def add_user_orders(self, user):
        """Ajoute un user dans la liste des orders"""
        self.mongoDb.orders.insert({'name': '{}'.format(user)})

    def delete_user_orders(self, user):
        """Supprime un user de la liste des orders"""
        self.mongoDb.orders.delete_one({'name': '{}'.format(user)})

    def ask_baguette(self):
        """ Demande aux gens s'ils veulent une baguette """
        users = self.get_users_notif()
        orders = self.get_users_orders()
        chase = self.get_users_chase()

        if self.first_round:
            results = [user for user in users if user not in orders]
        else:
            results = [user for user in users if user not in orders or user not in chase]

        self.send(text="Coucou tout le monde! Voulez vous une baguette {} ?".format(
            ' '.join(map(str, results))),
            user=self.room,
            message_type="groupchat")

    @botcmd
    def baguette(self, mess, args):
        """Tout pour commande une baguette"""
        actions = {
            'commande': self.commande,
            'annule': self.annule,
            'liste': self.liste,
            'notif': self.notif,
            'liste-notif': self.list_notif,
            'no-notif': self.no_notif,
            'chase' : self.chase,
            'no-chase': self.no_chase,
            'liste-chase': self.list_chase
        }
        commands = '\n'.join(['%s baguette %s (%s)' % (self.nick, action_name, action_def.__doc__) for action_name, action_def in actions.iteritems()])
        actions[''] = lambda *args: '%s\n%s' % ('Tu veux dire quoi ?', commands)

        def default_action(*args):
            return '%s\n%s' % ('Je ne cromprends pas', commands)
        self.send_simple_reply(mess, actions.get(args.strip(), default_action)(mess, args))

    @botcmd
    def oui(self, mess, args):
        """ Commander une baguette (shortcut) """
        return self.commande(mess, args)

    def commande(self, mess, args):
        """ Commander une baguette """
        user = mess.getFrom().getResource()
        orders = self.get_users_orders()
        if user not in orders:
            self.add_user_orders(user)

        return "OK!"

    def annule(self, mess, args):
        """ Annuler la commande d'une baguette """
        orders = self.get_users_orders()
        user = mess.getFrom().getResource()
        if user in orders:
            self.delete_user_orders(user)

        return "OK!"

    def liste(self, mess, args):
        """ Liste les gens qui veulent une baguette """
        orders = self.get_users_orders()

        return 'Liste des gens qui veulent une baguette: {}'.format(' '.join(orders))

    def notif(self, mess, args):
        """ Pour s'ajouter dans la liste des gens prevenus """
        users = self.get_users_notif()
        user = mess.getFrom().getResource()

        if user not in users:
            self.add_user_notif(user)
            return 'Ok, je te previendrai pour la prochaine commande de pain.'
        else:
            return 'Tu es deja dans la liste !'

    def no_notif(self, mess, args):
        """ Pour s'enlever de la liste des gens prevenus """
        users = self.get_users_notif()
        user = mess.getFrom().getResource()

        if user in users:
            self.delete_user_notif(user)
            return 'Ok, va te faire voir'
        else:
            return 'Beuh, pas dans la liste'

    def list_notif(self, mess, args):
        """ Liste les gens qui veulent etre prevenus de la prochaine commande """
        users = self.get_users_notif()
        return 'Liste des gens qui veulent etre prevenus de la prochaine commande: {}'.format(' '.join(map(str, users)))

    def chase(self, mess, args):
        """ Pour s'ajouter dans la liste des gens prevenus """
        users = self.get_users_chase()
        user = mess.getFrom().getResource()

        if user not in users:
            self.add_user_chase(user)
            return 'Ok, je te harcelerai pour la prochaine commande de pain.'
        else:
            return 'Tu es deja dans la chasing liste !'

    def no_chase(self, mess, args):
        """ Qu'il arrete de sonner trois fois le matin """
        users = self.get_users_chase()
        user = mess.getFrom().getResource()

        if user in users:
            self.delete_user_chase(user)
            return 'Ok, va te faire voir'
        else:
            return 'Beuh, pas dans la chasing liste'

    def list_chase(self, mess, args):
        """ Liste des relous qui savent pas répondre a un message et qui se plaignent de pas avoir de baguette !!"""
        users = self.get_users_chase()
        return 'Liste des relous qui savent pas répondre a un message et qui se plaignent de pas avoir de baguette !!{}'.format(' '.join(map(str, users)))

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
    def insulte(self, mess, args):
        """Insulte quelqu'un"""
        # Lire une insulte
        collection = self.mongoDb.insultes
        elt = collection.aggregate([{'$sample': {'size': 1}}])
        insulte = list(elt)[0]['text']

        # Qui instulter?
        if args and self.nick not in args:
            self.send_simple_reply(mess, u'{}'.format(
                insulte.replace("%guy%", args
                                )))
        else:
            self.send_simple_reply(mess, u'{}'.format(
                insulte.replace("%guy%", mess.getFrom().getResource()
                                )))

    @botcmd
    def resto(self, mess, args):
        """ Retourne les menus de resto """
        actions = {'piment': self.piment, 'eaty': self.eaty}
        list_of_resto = '\n'.join(['%s resto %s' % (self.nick, rest) for rest in actions.keys()])
        actions[''] = lambda: '%s\n%s' % ('Tu veux dire quoi ?', list_of_resto)

        def default_action():
            return '%s\n%s' % ('Je ne cromprends pas', list_of_resto)

        self.send_simple_reply(mess, actions.get(args.strip(), default_action)())

    @staticmethod
    def eaty():
        """Eaty menu"""
        # Retrieve menu
        req = requests.get('http://www.eatyfr.wordpress.com')
        if req.status_code == 200:
            menus = []
            soup = BeautifulSoup(req.text, "html.parser")
            for i in soup.find('div', attrs={'class': 'entry-content'}).findAll("h3")[1:]:
                menu = i.text.strip()
                if not menu.startswith(u'°') and menu != '':
                    menus.append(menu.encode("utf-8"))
            return 'Voici les menus Eaty du jour:\n{}'.format('\n'.join(menus))
        return 'Eaty est malade...'

    @staticmethod
    def piment():
        """Piment menu"""
        week_day = datetime.datetime.now().weekday()

        description = {
            u"BA MI": u"Nouilles de blé, crevettes marinées, raviolis frits, légumes, crudité, sauce sucrée",
            u"Soupe raviolis": u"Nouilles chinoises, raviolis aux crevettes, poulet, herbes aromatiques, soja",
            u"Bo Bun": u"Vermicelles de riz, boeuf woké au curry, cacahuètes concassées, nems, crudités",
            u"Pad Thai": u"Pâtes de riz, poulet, tofu, cacahuètes concassées, soja, ciboulette, sauce caramélisée",
            u"Ragoût vietnamien": u"Pâtes de riz, assortiment de boeuf, herbes aromatiques, bouillon de boeuf"}

        menu = {0: [u'BA MI'],
                1: [u'Soupe raviolis'],
                2: [u'Bo Bun'],
                3: [u'Bo Bun'],
                4: [u'Pad Thai', u'Ragoût vietnamien']}

        if week_day > 4:
            return "Eh oh... J'suis en week end moi reviens lundi"
        return u"Aujourd'hui le menu de piment rouge est \n%s" % '\n'.join(
            [u'%s => %s' % (ele, description[ele]) for ele in
             menu[week_day]])

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
    def kaamelott(self, mess, args):
        """Kaamelott"""
        base_url = 'http://kaamelott.underfloor.io/quote/rand'
        req = requests.get(base_url)
        if req.status_code == 200:
            self.send_simple_reply(mess, u'%s: "%s"' % (
                req.json().get('character', 'Perceval'), req.json().get('quote', "C'est pas faux")))
        else:
            self.send_simple_reply(mess, "J'ai été pas mal malade")


def read_password(username):
    """Read password from $HOME/.p or environment variable"""
    if 'BOT_PASSWORD' in os.environ:
        return os.environ['BOT_PASSWORD']
    try:
        with open(os.environ['HOME'] + "/.p", "r+") as current_file:
            for line in current_file.readlines():
                current_tuple = line.split(":")
                if current_tuple[0] == username:
                    return current_tuple[1].rstrip()
        print 'No password found'
    except IOError:
        print("Cannot find the poezio configuration file needed for password")
        sys.exit(1)
    return ''


def read_mongo_password():
    """Read password from environment variable"""
    return os.environ.get('MONGO_PASSWORD', '')


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
    password = read_password(main_args.username)
    bot = BaguetteJabberBot(main_args.username, password)
    bot.room = main_args.room
    bot.fromm = main_args.fromm
    bot.mail_to = main_args.to
    bot.subject = main_args.subject
    bot.nick = main_args.nick
    bot.mongoDb = bot.connect_mongo(main_args.mongoUser, read_mongo_password(), main_args.mongoUrl)
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
