from OVHJabberBot.bot import BaguetteJabberBot

import requests
import HTMLParser
from jabberbot import botcmd

@botcmd
def gif(mess, args):
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
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, pars.unescape(fact['data']['image_original_url']))
    else:
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, 'Giphy est malade...')
