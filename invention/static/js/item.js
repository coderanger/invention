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

    this.on('change:encryptionSkill change:coreSkill1 change:coreSkill2 change:metaLevel change:decryptorChance', this.calculateInventionChance, this);
    this.calculateInventionChance();

    this.set('metas', new Backbone.Collection(this.get('metas'), {comparator: 'meta_level'}));
    this.set('requirements', new collections.Requirements(this.get('requirements'), {}).on('change:total', function() { this.trigger('change change:requirements'); }, this));
  },
  defaults: function() {
    return {
      baseInventionChance: 0,
      metaLevel: 0,
      decryptorChance: 1,
      inventionChance: 0,
    }
  },
  calculateInventionChance: function() {
    var Base_Chance = +this.get('baseInventionChance'),
        Encryption_Skill_Level = +this.get('encryptionSkill').get('level'),
        Datacore_1_Skill_Level = +this.get('coreSkill1').get('level'),
        Datacore_2_Skill_Level = +this.get('coreSkill2').get('level'),
        Meta_Level = +this.get('metaLevel'),
        Decryptor_Modifier = +this.get('decryptorChance');
    var Invention_Chance = Base_Chance * (1 + (0.01 * Encryption_Skill_Level)) * (1 + ((Datacore_1_Skill_Level + Datacore_2_Skill_Level) * (0.1 / (5 - Meta_Level)))) * Decryptor_Modifier;
    this.set('inventionChance', Invention_Chance);
  }
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
    'change #metas select': 'updateMeta'
  },
  initialize: function() {
    this.setViews({
      '#encryptionSkillLevel': new views.SkillLevel({model: this.model.get('encryptionSkill')}),
      '#coreSkillLevel1': new views.SkillLevel({model: this.model.get('coreSkill1')}),
      '#coreSkillLevel2': new views.SkillLevel({model: this.model.get('coreSkill2')}),
    });
    this.model.on('change', this.render, this);
  },
  data: function() {
    return this.model.attributes;
  },
  afterRender: function() {
    this.$('#metas select').val(this.model.get('metaLevel'));
  },
  updateMeta: function(evt) {
    this.model.set('metaLevel', $(evt.target).val());
  }
});

views.Materials = Backbone.LayoutView.extend({
  template: '#materials-template',
  initialize: function() {
    this.model.on('change:requirements change:metaLevel', this.render, this);
  },
  data: function() {
    var metaLevel = this.model.get('metaLevel'), originalReqs = this.model.get('requirements');
    var reqs = new collections.Requirements(originalReqs.models, {});
    if(metaLevel != '0') {
      var metaItem = this.model.get('metas').find(function(item) { return item.get('meta_level') == metaLevel; });
      reqs.add({item_id: metaItem.id, quantity: 1, item: metaItem.attributes});
    }
    return {requirements: reqs};
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
