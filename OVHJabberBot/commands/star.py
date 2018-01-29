from OVHJabberBot.bot import BaguetteJabberBot

from jabberbot import botcmd
import requests
import datetime

@botcmd
def star(mess, args):
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
            BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, u'Voici les prochains bus:\n{}'.format('\n'.join(bus)))
        else:
            BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, "Il n'y a pas de bus prochainement")
    else:
        BaguetteJabberBot.send_simple_reply(BaguetteJabberBot(), mess, 'star est malade...')