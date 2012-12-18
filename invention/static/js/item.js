Backbone.LayoutManager.configure({
  fetch: function(path) {
    return _.template(path[0] === '<' ? path : $(path).html());
  },
  render: function(template, context) {
    context || (context = {});
    _.extend(context, helpers);
    return template(context);
  }
});

var helpers = {};
helpers.percent = function(n) { return (n*100).toFixed(2) + '%'; };
helpers.price = function(n) { return (+n).toFixed(2); };

var models = {};
models.Skill = Backbone.Model.extend({
  initialize: function() {
    this.set('level', localStorage.getItem('skills:'+this.get('name')) || 4);
    this.on('change:level', function(model, value) { localStorage.setItem('skills:'+model.get('name'), value)});
  }
});

models.Item = Backbone.Model.extend({});

models.Requirement = Backbone.Model.extend({
  idAttribute: 'item_id',
  defaults: {damage_per_job: 1},
  initialize: function(attibutes, options) {
    this.set({
      item: new models.Item(this.get('item')),
      count: this.get('quantity') * this.get('damage_per_job')
    });
    this.calculatePrice();
  },
  calculatePrice: function() {
    var price = this.get('item').get('prices').min_sell,
        subtotal = this.get('count') * price;
    this.set({
      price: price,
      subtotal: subtotal,
    });
  }
});

models.Invention = Backbone.Model.extend({
  initialize: function() {
    this.set('encryptionSkill', new models.Skill({name: this.get('encryptionSkill')}).on('change', function() { this.trigger('change change:encryptionSkill'); }, this));
    this.set('coreSkill1', new models.Skill({name: this.get('coreSkill1')}).on('change', function() { this.trigger('change change:coreSkill1'); }, this));
    this.set('coreSkill2', new models.Skill({name: this.get('coreSkill2')}).on('change', function() { this.trigger('change change:coreSkill2'); }, this));

    this.on('change:encryptionSkill change:coreSkill1 change:coreSkill2 change:metaLevel change:decryptor', this.calculateInventionChance, this);
    this.calculateInventionChance();

    this.set({
      metas: new Backbone.Collection(this.get('metas'), {model: models.Item, comparator: 'meta_level'}),
      requirements: new collections.Requirements(this.get('requirements'), {}).on('change:total', function() { this.trigger('change change:requirements'); }, this),
      decryptors: new Backbone.Collection(this.get('decryptors'), {model: models.Item})
    });
    this.on('change:requirements change:metaLevel change:decryptor', this.calculateRequirements, this);
    this.calculateRequirements();
  },
  defaults: function() {
    return {
      baseInventionChance: 0,
      metaLevel: 0,
      decryptor: 0,
      inventionChance: 0,
    }
  },
  calculateInventionChance: function() {
    var Base_Chance = +this.get('baseInventionChance'),
        Encryption_Skill_Level = +this.get('encryptionSkill').get('level'),
        Datacore_1_Skill_Level = +this.get('coreSkill1').get('level'),
        Datacore_2_Skill_Level = +this.get('coreSkill2').get('level'),
        Meta_Level = +this.get('metaLevel'),
        Decryptor_Modifier = this.decryptorData[this.get('decryptor')].chance;
    var Invention_Chance = Base_Chance * (1 + (0.01 * Encryption_Skill_Level)) * (1 + ((Datacore_1_Skill_Level + Datacore_2_Skill_Level) * (0.1 / (5 - Meta_Level)))) * Decryptor_Modifier;
    this.set('inventionChance', Invention_Chance);
  },
  calculateRequirements: function() {
    var metaLevel = this.get('metaLevel');
    var reqs = new collections.Requirements(this.get('requirements').models, {});
    if(metaLevel != '0') {
      var metaItem = this.get('metas').find(function(item) { return item.get('meta_level') == metaLevel; });
      reqs.add({item_id: metaItem.id, quantity: 1, item: metaItem.attributes});
    }
    var decryptor = this.get('decryptor');
    if(decryptor != '0') {
      var decryptorItem = this.get('decryptors').at(decryptor - 1);
      reqs.add({item_id: decryptorItem.id, quantity: 1, item: decryptorItem.attributes});
    }
    this.set('fullRequirements', reqs);
  },
  decryptorData: [
    {chance: 1.0, runs: 0, me:  0, pe: 0},
    {chance: 0.6, runs: 9, me: -2, pe: 1},
    {chance: 1.0, runs: 2, me:  1, pe: 4},
    {chance: 1.1, runs: 0, me:  2, pe: 3},
    {chance: 1.2, runs: 1, me:  3, pe: 5},
    {chance: 1.8, runs: 4, me: -1, pe: 2}
  ]
});

var collections = {};
collections.Requirements = Backbone.Collection.extend({
  model: models.Requirement,
  initialize: function(models, options) {
    this.total = 0;
    this.on('reset add remove change:subtotal', this.calculatePrice, this);
    options.silent = false; // Force an update for calc price
  },
  calculatePrice: function() {
    var total = this.reduce(function(memo, req){ return memo + (req.get('subtotal') || 0); }, 0);
    if(total !== this.total) {
      this.total = total;
      this.trigger('change change:total');
    }
    return this;
  }
});

var views = {};
views.SkillLevel = Backbone.LayoutView.extend({
  tagName: 'select',
  className: 'skill-level',
  template: '<option value="0">Not Trained</option><option value="1">1</option><option value="2">2</option>' + 
            '<option value="3">3</option><option value="4">4</option><option value="5">5</option>',
  events: {'change': 'updateLevel'},
  afterRender: function() {
    this.$el.val(this.model.get('level'));
  },
  updateLevel: function() {
    this.model.set('level', this.$el.val());
  }
});

views.InventionChance = Backbone.LayoutView.extend({
  template: '#invention-chance-template',
  events: {
    'change #metas select': 'updateMeta',
    'click .btn-decryptor': 'updateDecryptor'
  },
  initialize: function() {
    this.setViews({
      '#encryptionSkillLevel': new views.SkillLevel({model: this.model.get('encryptionSkill')}),
      '#coreSkillLevel1': new views.SkillLevel({model: this.model.get('coreSkill1')}),
      '#coreSkillLevel2': new views.SkillLevel({model: this.model.get('coreSkill2')}),
    });
    this.model.on('change change:decryptor', this.render, this);
  },
  data: function() {
    return _.extend(this.model.attributes, {decryptorData: this.model.decryptorData});
  },
  afterRender: function() {
    this.$('#metas select').val(this.model.get('metaLevel'));
    this.$('.btn-decryptor').removeClass('btn-primary').eq(this.model.get('decryptor')).addClass('btn-primary');
  },
  updateMeta: function(evt) {
    this.model.set('metaLevel', $(evt.target).val());
  },
  updateDecryptor: function(evt) {
    this.model.set('decryptor', $(evt.target).data('n'));
  }
});

views.Materials = Backbone.LayoutView.extend({
  template: '#materials-template',
  initialize: function() {
    this.model.on('change:requirements change:metaLevel change:decryptor', this.render, this);
  },
  data: function() {
    return {requirements: this.model.get('fullRequirements')};
  }
});

views.InventionOverview = Backbone.LayoutView.extend({
  template: '#invention-overview-template',
  initialize: function() {
    this.model.on('change:requirements change:inventionChance', this.render, this);
  },
  data: function() {
    return {
      total: this.model.get('requirements').total,
      inventionChance: this.model.get('inventionChance')
    };
  }
});

views.Application = Backbone.LayoutView.extend({
  template: '<div id="invention-chance"></div><div class="row"><div id="materials"></div><div id="overview"></div></div>',
  initialize: function() {
    this.setView('#invention-chance', new views.InventionChance({model: this.model}));
    this.setView('#materials', new views.Materials({model: this.model}));
    this.setView('#overview', new views.InventionOverview({model: this.model}));
  }
});
