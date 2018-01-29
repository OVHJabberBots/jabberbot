# coding: utf-8
from OVHJabberBot.bot import BaguetteJabberBot

from jabberbot import botcmd
import requests
from bs4 import BeautifulSoup
import datetime

@botcmd
def resto(mess, args):
    """ Retourne les menus de resto """
    actions = {'piment': piment, 'eaty': eaty}
    list_of_resto = '\n'.join(['%s resto %s' % (BaguetteJabberBot().nick, rest) for rest in actions.keys()])
    actions[''] = lambda: '%s\n%s' % ('Tu veux dire quoi ?', list_of_resto)

    def default_action():
        return '%s\n%s' % ('Je ne cromprends pas', list_of_resto)

    BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, actions.get(args.strip(), default_action)())


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