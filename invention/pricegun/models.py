import datetime
from xml.etree import ElementTree

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
import requests

class ItemPricesManager(models.Manager):
    def for_items(self, items, region, force=False):
        prices = dict((price.item_id, price) for price in self.filter(item_id__in=items, region=region))
        outdated = dict((item_id, price) for item_id, price in prices.iteritems() if force or now() - price.updated_at >= datetime.timedelta(days=1))
        for i in items:
            if i not in prices:
                prices[i] = outdated[i] = self.model(item_id=i, region=region)
        if outdated:
            params = {'regionlimit': region, 'typeid': outdated.keys()}
            response = requests.get('http://api.eve-central.com/api/marketstat', params=params)
            response.raise_for_status()
            tree = ElementTree.fromstring(response.text)
            for item in tree.findall('.//type'):
                price = outdated[int(item.attrib['id'])]
                price.mean_sell = item.find('./sell/avg').text
                price.mean_buy = item.find('./buy/avg').text
                price.mean_all = item.find('./all/avg').text
                price.median_sell = item.find('./sell/median').text
                price.median_buy = item.find('./buy/median').text
                price.median_all = item.find('./all/median').text
                price.min_sell = item.find('./sell/min').text
                price.max_buy = item.find('./buy/max').text
                price.save()
        return prices

class ItemPrices(models.Model):
    item_id = models.IntegerField()
    region = models.IntegerField(_('Region'))
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    mean_sell = models.DecimalField(_('Mean Sell Price'), max_digits=16, decimal_places=2, default=0)
    mean_buy = models.DecimalField(_('Mean Buy Price'), max_digits=16, decimal_places=2, default=0)
    mean_all = models.DecimalField(_('Mean Price'), max_digits=16, decimal_places=2, default=0)
    median_sell = models.DecimalField(_('Median Sell Price'), max_digits=16, decimal_places=2, default=0)
    median_buy = models.DecimalField(_('Median Buy Price'), max_digits=16, decimal_places=2, default=0)
    median_all = models.DecimalField(_('Median Price'), max_digits=16, decimal_places=2, default=0)
    min_sell = models.DecimalField(_('Minimum Sell Price'), max_digits=16, decimal_places=2, default=0)
    max_buy = models.DecimalField(_('Maximum Buy Price'), max_digits=16, decimal_places=2, default=0)

    objects = ItemPricesManager()

    def to_dict(self):
        return {
            'mean_sell': self.mean_sell,
            'mean_buy': self.mean_buy,
            'mean_all': self.mean_all,
            'median_sell': self.median_sell,
            'median_buy': self.median_buy,
            'median_all': self.median_all,
            'min_sell': self.min_sell,
            'max_buy': self.max_buy,
        }
