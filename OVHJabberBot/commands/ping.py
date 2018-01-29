from OVHJabberBot.bot import BaguetteJabberBot

from jabberbot import botcmd

@botcmd
def ping(mess, args):
    """ Tu veux jouer ? """
    BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, 'pong')