# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ItemPrices'
        db.create_table('pricegun_itemprices', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item_id', self.gf('django.db.models.fields.IntegerField')()),
            ('region', self.gf('django.db.models.fields.IntegerField')()),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('mean_sell', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('mean_buy', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('mean_all', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('median_sell', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('median_buy', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('median_all', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('min_sell', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
            ('max_buy', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=2)),
        ))
        db.send_create_signal('pricegun', ['ItemPrices'])


    def backwards(self, orm):
        # Deleting model 'ItemPrices'
        db.delete_table('pricegun_itemprices')


    models = {
        'pricegun.itemprices': {
            'Meta': {'object_name': 'ItemPrices'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {}),
            'max_buy': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'mean_all': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'mean_buy': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'mean_sell': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'median_all': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'median_buy': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'median_sell': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'min_sell': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'region': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricegun']