from OVHJabberBot.bot import BaguetteJabberBot

from OVHJabberBot.db.insulte import Insulte
from jabberbot import botcmd


@botcmd
def insulte(mess, args):
    """Insulte quelqu'un"""
    # Lire une insulte
    insulte = list(Insulte.objects().aggregate(*[{'$sample': {'size': 1}}]))[0]['text']

    # Qui instulter?
    if args and BaguetteJabberBot().nick not in args:
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, u'{}'.format(
            insulte.replace("%guy%", args
                            )))
    else:
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, u'{}'.format(
            insulte.replace("%guy%", mess.getFrom().getResource()
                            )))
