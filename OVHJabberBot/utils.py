# coding: utf-8

import os
import yaml
import smtplib
from email.mime.text import MIMEText


def parse_args():
    """
    Parse command line args
    """
    with open(os.environ['HOME'] + "/.config/boulanger.conf") as f:
        config = yaml.load(f)

    return config['config']


def sendmail(mail_to, orders):
    """ Send email """
    msg = MIMEText(
        "Bonjour Marie,\nEst-il possible de rapporter {} baguettes aujourd'hui ?"
        "\n\nDemandeurs :\n{}".format(
            len(orders), '\n'.join([name for name in orders])))
    msg['Subject'] = 'Commande de pain OVH'
    msg['From'] = 'robot boulanger'
    msg['To'] = mail_to

    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(msg['From'], [mail_to], msg.as_string())
    smtp.quit()
