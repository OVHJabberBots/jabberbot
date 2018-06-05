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
Instead of providing all parameters, you can put them in a file as key=value. It's looking at ~/.config/boulanger.ini by default but the path can be overrided by the -c.

## Dev

1. Install vagrant http://vagrantup.com
2. Install virtualbox
3. Run `vagrant up` in the repository base folder
4. virtualenv venv
5. source venv/bin/activate
6. pip install -r requirements.txt


Pidgin client is tested succesfully against the vagrant installation.

Login is admin and password admin.

Access the vm via `vagrant ssh`, get root by `sudo -s`



``` bash
python -m OVHJabberBot --username admin@localhost --room test@conference.localhost --mongoUrl localhost/boulanger
```
