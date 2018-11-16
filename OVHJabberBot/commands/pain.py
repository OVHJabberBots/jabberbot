# coding: utf-8


class Pain(object):
    def __init__(self):
        self.orders = []

    def oui(self, username):
        """ Commander une baguette """
        if username not in self.orders:
            self.orders.append(username)

    def non(self, username):
        """ Annuler la commande d'une baguette """
        if username in self.orders:
            self.orders.delete(username)

    def list_orders(self):
        """ Liste les gens qui veulent une baguette """
        return 'Liste des gens qui veulent une baguette: {}'.format(' '.join([name for name in self.orders]))
