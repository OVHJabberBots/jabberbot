from utils import parse_args,read_password
from bot import BaguetteJabberBot
import inspect
import db
import commands

import re

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
    # create a regex to check if a message is a direct message
    bot.direct_message_re = re.compile(r'^%s?[^\w]?' % main_args.nick)
    db.connection(main_args.mongoUrl, main_args.mongoUser, main_args.mongoPass)

    for modname,module in inspect.getmembers(commands, inspect.ismodule):
        if modname in ('base', 'pkgutil'):
            continue
        for cmdname,function  in inspect.getmembers(module, inspect.isfunction):
            if getattr(function, '_jabberbot_command', False):
                bot.register_command(cmdname, function)

    try:
        bot.muc_join_room(main_args.room, main_args.nick)
    except AttributeError:
        # Connection error is check after
        pass
    bot.serve_forever()


if __name__ == '__main__':
    main()
