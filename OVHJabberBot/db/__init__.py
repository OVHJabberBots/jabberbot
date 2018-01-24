from mongoengine import connect

def connection(url, username=None, password=None):
    print password
    if username is not None:
        connectString = 'mongodb://' + username + ':' + password + '@' + url
    else:
        connectString = 'mongodb://' + url

    connect("boulanger", host=connectString)
