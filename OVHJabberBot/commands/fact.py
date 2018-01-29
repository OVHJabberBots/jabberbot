from OVHJabberBot.bot import BaguetteJabberBot

import requests
import HTMLParser
from jabberbot import botcmd

@botcmd
def fact(mess, args):
    """ Chuck Norris Facts """
    # Retrieve a fact
    req = requests.get('http://www.chucknorrisfacts.fr/api/get?data=tri:alea;nb:1')
    pars = HTMLParser.HTMLParser()
    if req.status_code == 200:
        fact = req.json()
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, pars.unescape(fact[0]['fact']))
    else:
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, 'Chuck Norris est malade...')