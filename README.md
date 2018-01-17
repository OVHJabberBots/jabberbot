# jabberbot

## Install

``` bash
pip install --user --pre -r requirements.txt
```

## Configure

Create a configuration file in ~/.p
Set it like
```
myuser@mydomain:mypassword
```
Or you can use the BOT_PASSWORD EnvVar to supply your jabber password

## Usage

``` bash
export BOT_PASSWORD= & export MONGO_PASSWORD= & ./bot.py --username firstname.lastname@yourdomain --room room@conference.jabber.ovh.net --mongoUrl yourmongo
```


## Dev
Via the vagrant VM
``` bash
export BOT_PASSWORD=admin & export MONGO_PASSWORD="" & ./bot.py --username admin --room test@localhost --mongoUrl localhost/boulanger
```
