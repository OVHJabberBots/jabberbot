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
python -m OVHJabberBot --username firstname.lastname@yourdomain --room room@conference --mongoUser boulanger --mongoPass --...
```


## Dev
Via the vagrant VM
``` bash
python -m OVHJabberBot --username admin@localhost --room test@conference.localhost --mongoUrl localhost/boulanger
```
