# coding: utf-8
from OVHJabberBot.bot import BaguetteJabberBot
from OVHJabberBot.db.order import Order
from OVHJabberBot.db.notif import Notif

from jabberbot import botcmd

import schedule
import smtplib
from email.mime.text import MIMEText


@botcmd
def baguette(mess, args):
    """Tout pour commande une baguette"""
    actions = {
        'commande': order,
        'annule': cancel,
        'liste': list_orders,
        'notif': notif,
        'list-notif': list_notif,
        'no-notif': no_notif,
    }
    commands = '\n'.join(
        ['%s baguette %s (%s)' % (BaguetteJabberBot().nick, action_name, action_def.__doc__) for action_name, action_def in
         actions.iteritems()])
    actions[''] = lambda *args: '%s\n%s' % ('Tu veux dire quoi ?', commands)

    def default_action(*args):
        return '%s\n%s' % ('Je ne cromprends pas', commands)

    BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, actions.get(args.strip(), default_action)(mess, args))


@botcmd
def oui(mess, args):
    """ Commander une baguette (shortcut) """
    return order(mess, args)


def init():
    schedule.every().monday.at("09:00").do(ask_baguette)
    schedule.every().monday.at("09:15").do(ask_baguette)
    schedule.every().monday.at("09:30").do(ask_baguette)
    schedule.every().monday.at("09:45").do(sendmail)
    schedule.every().thursday.at("09:00").do(ask_baguette)
    schedule.every().thursday.at("09:15").do(ask_baguette)
    schedule.every().thursday.at("09:30").do(ask_baguette)
    schedule.every().thursday.at("09:45").do(sendmail)


def order(mess, args):
    """ Commander une baguette """
    username = mess.getFrom().getResource()
    order = Order.objects(name=username).first()
    if order is None:
        order = Order(name=username)
        order.save()
        return 'Ok!'

    return "T'as déjà passé une commande !"


def cancel(mess, args):
    """ Annuler la commande d'une baguette """
    username = mess.getFrom().getResource()
    order = Order.objects(name=username).first()

    if order is not None:
        order.delete()
        return 'Ok, j\'efface ta commande'

    return 'T\'avais meme pas passe commande ...'


def list_orders(mess, args):
    """ Liste les gens qui veulent une baguette """
    orders = Order.objects()

    return 'Liste des gens qui veulent une baguette: {}'.format(' '.join([o.name for o in orders]))


def notif(mess, args):
    """ Pour s'ajouter dans la liste des gens prevenus """
    username = mess.getFrom().getResource()
    notif = Notif.objects(name=username).first()

    if notif is None:
        notif = Notif(name=username)
        notif.save()
        return 'Ok, je te previendrai pour la prochaine commande de pain.'

    return 'Tu es deja dans la liste !'


def no_notif(mess, args):
    """ Pour s'enlever de la liste des gens prevenus """
    username = mess.getFrom().getResource()
    notif = Notif.objects(name=username).first()

    if notif is not None:
        notif.delete()
        return 'Ok, va te faire voir'

    return 'Beuh, t\'es pas dans la liste'


def list_notif(mess, args):
    """ Liste les gens qui veulent etre prevenus de la prochaine commande """
    notifs = Notif.objects()
    return 'Liste des gens qui veulent etre prevenus de la prochaine commande: {}'.format(
        ' '.join([n.name for n in notifs]))


def ask_baguette():
    """ Demande aux gens s'ils veulent une baguette """
    orders = Order.objects()
    notifs = Notif.objects()

    results = [user.name for user in notifs if user not in [order.name for order in orders]]

    BaguetteJabberBot.send(BaguetteJabberBot(), text="Coucou tout le monde! Voulez vous une baguette {} ?".format(
        ' '.join(map(str, results))),
        user=BaguetteJabberBot().room,
        message_type="groupchat")


def sendmail():
    """ Send email """
    orders = Order.objects()

    if orders:
        msg = MIMEText(
            "Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?"
            "\n\nDemandeurs :\n{}".format(
                len(orders), '\n'.join([o.name for o in orders])))
        msg['Subject'] = BaguetteJabberBot().subject
        msg['From'] = BaguetteJabberBot().fromm
        msg['To'] = BaguetteJabberBot().mail_to

        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(BaguetteJabberBot().fromm, [BaguetteJabberBot().mail_to], msg.as_string())
        smtp.quit()

        BaguetteJabberBot.send(BaguetteJabberBot(), text="J'ai envoye la commande a Marie ! cc {}".format(" ".join([o.name for o in orders])),
                  user=BaguetteJabberBot().room, message_type="groupchat")

        Order.drop_collection()
    else:
        BaguetteJabberBot.send(BaguetteJabberBot(), text="Pas de commande aujourd'hui !",
                  user=BaguetteJabberBot().room,
                  message_type="groupchat")
