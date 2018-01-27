import configargparse

import os

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


def parse_args():
    """
    Parse command line args
    """
    parser = configargparse.ArgParser(default_config_files=["~/.config/boulanger.conf"])
    parser.add("-c",
               is_config_file=True,
               help="Path to the configuration file")
    parser.add("--username",
                        required=True,
                        help="Your jabber username")
    parser.add("--room",
                        help="Room to join. Default is pcr@conference.jabber.ovh.net",
                        default="pcr@conference.jabber.ovh.net")
    parser.add("--nick",
                        help="Nick name to show. Default is Boulanger",
                        default="Boulanger")
    parser.add("--password",
                        help="Your jabber password")
    parser.add("--fromm",
                        help="Mail address to send from")
    parser.add("--to",
                        help="Mail address to send to")
    parser.add("--subject",
                        help="Subject of mail. Default is Commande de baguette",
                        default="Commande de baguette")
    parser.add("--mongoUser",
                        help="Mongo db user",
                        default=None)
    parser.add("--mongoPass",
                        help="Mongo db password",
                        default=None)
    parser.add("--mongoUrl",
                        help="Mongo db user",
                        default="ds125183.mlab.com:25183/boulanger")
    return parser.parse_args()

