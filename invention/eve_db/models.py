from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

class ItemManager(models.Manager):
    @property
    def purchaseable(self):
        return self.filter(market_group_id__isnull=False)

    def inventable(self, count=None, qs=None):
        results = []
        qs = qs or self.purchaseable
        qs = qs.only('id', 'name', 'group_id')
        for item in qs:
            if item.invention_chance > 0:
                results.append(item)
                if count and len(results) >= count:
                    break
        return results

class Item(models.Model):
    """
    Inventory types are generally objects that can be carried in your
    inventory (with the exception of suns, moons, planets, etc.) These are mostly
    market items, along with some basic attributes of each that are common
    to all items. 
    """
    id = models.IntegerField(unique=True, primary_key=True, db_column='typeID')
    name = models.CharField(max_length=100, blank=True, db_column='typeName')
    description = models.TextField(blank=True, db_column='description')
    group_id = models.IntegerField(null=True, db_column='groupID')
    market_group_id = models.IntegerField(null=True, db_column='marketGroupID')
    published = models.IntegerField(null=True, db_column='published')

    objects = ItemManager()

    class Meta:
        db_table = 'invTypes'
        verbose_name = _('Inventory Type')
        verbose_name_plural = _('Inventory Types')
        managed = False

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)

    @cached_property
    def invention_chance(self):
        # Item-specific
        chance = {
            17476: 0.2,
            17478: 0.25,
            17480: 0.3,
        }.get(self.id)
        if chance:
            return chance
        # Groups
        chance = {
            419: 0.2,
            27: 0.2,
            26: 0.25,
            28: 0.25,
            25: 0.3,
            420: 0.3,
            513: 0.3,
        }.get(self.group_id)
        if chance:
            return chance
        # Check if a Tech2 version of this item exists
        if ItemMeta.objects.filter(parent=self, meta_group_id=2).exists():
            return 0.4
        return 0

    @cached_property
    def meta_level(self):
        try:
            return self.attributes.get(attribute_id=633).value
        except ItemAttributes.DoesNotExist:
            return 0

    def get_absolute_url(self):
        return reverse('invention', args=(str(self.id), self.slug))

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'meta_level': self.meta_level}

class ItemMeta(models.Model):
    """
    Relation between different variants of item (i.e. Tech-I, Faction, Tech-II).
    These are not "meta-levels" of items used for calculate invention success.
    For that information see Attribute metaLevel (attributeID=633) in table
    dgmTypeAttributes linked with typeID in question.
    """
    item = models.ForeignKey(Item, primary_key=True, related_name='+', db_column='typeID')
    parent = models.ForeignKey(Item, null=True, related_name='+', db_column='parentTypeID')
    meta_group_id = models.IntegerField(null=True, db_column='metaGroupID')

    class Meta:
        db_table = 'invMetaTypes'
        verbose_name = _('Inventory Meta')
        verbose_name_plural = _('Inventory Metas')
        managed = False

class ItemAttributes(models.Model):
    item = models.ForeignKey(Item, primary_key=True, related_name='attributes', db_column='typeID')
    attribute_id = models.IntegerField(db_column='attributeID')
    value_float = models.FloatField(null=True, db_column='valueFloat')
    value_int = models.IntegerField(null=True, db_column='valueInt')

    class Meta:
        db_table = 'dgmTypeAttributes'
        verbose_name = _('Item Attribute')
        verbose_name_plural = _('Item Attributes')
        managed = False

    @property
    def value(self):
        if self.value_float is None:
            return self.value_int
        else:
            return self.value_float

class Blueprint(models.Model):
    """
    Stores info about each kind of blueprint.
    """
    blueprint_item = models.OneToOneField(Item, unique=True, primary_key=True,
                                       related_name='+', db_column='blueprintTypeID')
    product_item = models.OneToOneField(Item, related_name='blueprint', db_column='productTypeID')
    # This is used for T2. Not always populated.
    parent_blueprint_item = models.ForeignKey(Item, blank=True, null=True,
                                              related_name='child_blueprints', db_column='parentBlueprintTypeID')
    production_time = models.IntegerField(blank=True, null=True, db_column='productionTime')
    tech_level = models.IntegerField(blank=True, null=True, db_column='techLevel')
    research_productivity_time = models.IntegerField(blank=True, null=True, db_column='researchProductivityTime')
    research_material_time = models.IntegerField(blank=True, null=True, db_column='researchMaterialTime')
    research_copy_time = models.IntegerField(blank=True, null=True, db_column='researchCopyTime')
    research_tech_time = models.IntegerField(blank=True, null=True, db_column='researchTechTime')
    productivity_modifier = models.IntegerField(blank=True, null=True, db_column='productivityModifier')
    material_modifier = models.IntegerField(blank=True, null=True, db_column='materialModifier')
    waste_factor = models.IntegerField(blank=True, null=True, db_column='wasteFactor')
    max_production_limit = models.IntegerField(blank=True, null=True, db_column='maxProductionLimit')

    @cached_property
    def invention_requirements(self):
        return self.requirements.filter(activity_id=8)

    class Meta:
        db_table = 'invBlueprintTypes'
        ordering = ['blueprint_item']
        verbose_name = _('Inventory Blueprint Type')
        verbose_name_plural = _('Inventory Blueprint Types')
        managed = False

    def __unicode__(self):
        return unicode(self.product_item)

class BlueprintRequirement(models.Model):
    """
    Extra items required by blueprints to build or research.
    """
    blueprint = models.ForeignKey(Blueprint, primary_key=True,
                                  related_name='requirements', db_column='typeID')
    activity_id = models.IntegerField(db_column='activityID') # Actually a foreign key, but I don't care
    item = models.ForeignKey(Item, related_name='+', db_column='requiredTypeID')
    quantity = models.IntegerField(db_column='quantity')
    damage_per_job = models.FloatField(db_column='damagePerJob')
    recycle = models.IntegerField(db_column='recycle')

    skill_map = {
        # Minmatar data interfaces
        25553: 'Minmatar Encryption Methods',
        25857: 'Minmatar Encryption Methods',
        26597: 'Minmatar Encryption Methods',
        # Caldari data interfaces
        25555: 'Caldari Encryption Methods',
        25853: 'Caldari Encryption Methods',
        26599: 'Caldari Encryption Methods',
        # Gallente data interfaces
        25556: 'Gallente Encryption Methods',
        25855: 'Gallente Encryption Methods',
        26601: 'Gallente Encryption Methods',
        # Amarr data interfaces
        25554: 'Amarr Encryption Methods',
        25851: 'Amarr Encryption Methods',
        26603: 'Amarr Encryption Methods',
        # Datacores
        11496: 'Defensive Subsystems Engineering',
        20114: 'Propulsion Subsystems Engineering',
        20115: 'Engineering Subsystems Engineering',
        20116: 'Electronic Subsystems Engineering',
        20171: 'Hydromagnetic Physics',
        20172: 'Minmatar Starship Engineering',
        20410: 'Gallentean Starship Engineering',
        20411: 'High Energy Physics',
        20412: 'Plasma Physics',
        20413: 'Laser Physics',
        20414: 'Quantum Physics',
        20415: 'Molecular Engineering',
        20416: 'Nanite Engineering',
        20417: 'Electromagnetic Physics',
        20418: 'Electronic Engineering',
        20419: 'Graviton Physics',
        20420: 'Rocket Science',
        20421: 'Amarrian Starship Engineering',
        20423: 'Nuclear Physics',
        20424: 'Mechanical Engineering',
        20425: 'Offensive Subsystems Engineering',
        25887: 'Caldari Starship Engineering',
    }

    class Meta:
        db_table = 'ramTypeRequirements'
        ordering = ['blueprint']
        verbose_name = _('Blueprint Requirement')
        verbose_name_plural = _('Blueprint Requirements')
        managed = False

    def __unicode__(self):
        return unicode(self.item)

    @cached_property
    def skill(self):
        return self.skill_map[self.item_id]

    def to_dict(self, item=None):
        damage = self.damage_per_job
        # Override the damage to data interfaces
        if self.skill and 'Encryption Methods' in self.skill:
            damage = 0
        data = {
            'item_id': self.item_id,
            'quantity': self.quantity,
            'damage_per_job': damage,
            'skill': self.skill,
        }
        if item:
            data['item'] = item
        return data

class Material(models.Model):
    """
    Material composition of items. This is used in reprocessing (when you have
    a stack of invTypes.portionSize), as well as in manufacturing (as materials
    affected by waste).
    """
    item = models.ForeignKey(Item, primary_key=True, related_name='+', db_column='typeID')
    material = models.ForeignKey(Item, related_name='materials', db_column='materialTypeID')
    quantity = models.IntegerField(db_column='quantity')

    class Meta:
        db_table = 'invTypeMaterials'
        ordering = ['item']
        verbose_name = _('Material')
        verbose_name_plural = _('Materials')
        managed = False

    def __unicode__(self):
        return unicode(self.material)
