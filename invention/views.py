from django.shortcuts import redirect
from django.template.response import TemplateResponse

from invention.eve_db.models import Item, ItemMeta
from invention.pricegun.models import ItemPrices
from invention.utils.json import JSONResponse

def index(request):
    return TemplateResponse(request, 'index.html', {})

def autocomplete(request):
    qs = Item.objects.purchaseable.filter(name__icontains=request.GET['query'])
    results = Item.objects.inventable(8, qs)
    return JSONResponse({'results': [item.name for item in results]})

def search(request):
    query = request.GET['q']
    try:
        exact = Item.objects.get(name=query)
        return redirect(exact)
    except Item.DoesNotExist:
        qs = Item.objects.purchaseable.filter(name__icontains=query)
        results = Item.objects.inventable(qs=qs)
        return TemplateResponse(request, 'search.html', {'items': results})

_decryptors = {
    'Amarr': [23181, 23180, 23178, 23179, 23182],
    'Caldari': [21576, 21575, 21573, 21574, 21577],
    'Gallente': [23186, 23185, 23183, 23184, 23187],
    'Minmatar': [21582, 21581, 21579, 21580, 21583],
}

def _items(items):
    prices = ItemPrices.objects.for_items([i.id for i in items], 10000002)
    output = []
    for item in items:
        json_data = item.to_dict()
        json_data['prices'] = prices[item.id].to_dict()
        output.append(json_data)
    return output

def invention(request, item_id, item_slug):
    item = Item.objects.get(id=item_id)
    if item.invention_chance == 0:
        return TemplateResponse(request, 'bad_item.html', {'item': item})
    # Find the encryption skill and the two datacore skills
    skills = [req.skill for req in item.blueprint.invention_requirements]
    encryption_skill = [s for s in skills if 'Encryption Methods' in s][0]
    skills.remove(encryption_skill)
    skills.sort()
    # Build the requirements data
    reqs = item.blueprint.invention_requirements
    req_items = _items([req.item for req in reqs])
    compiled_reqs = [req.to_dict(req_item) for req, req_item in zip(reqs, req_items)]
    # Find the right decryptors
    decryptor_ids = _decryptors[encryption_skill.split(' ', 1)[0]]
    decryptor_items = dict((i['id'], i) for i in _items(Item.objects.filter(id__in=decryptor_ids)))
    compiled_decryptors = [decryptor_items[i] for i in decryptor_ids]
    return TemplateResponse(request, 'item.html', {
        'item': item,
        'invention_data': {
            'baseInventionChance': item.invention_chance,
            'encryptionSkill': encryption_skill,
            'coreSkill1': skills[0],
            'coreSkill2': skills[1],
            'metas': _items([m.item for m in ItemMeta.objects.filter(parent=item, meta_group_id=1)]),
            'requirements': compiled_reqs,
            'decryptors': compiled_decryptors,
        },
    })

def items(request):
    items = Item.objects.filter(id__in=request.GET.getlist('id'))
    prices = ItemPrices.objects.for_items([i.id for i in items], 10000002)
    output = []
    for item in items:
        json_data = item.to_dict()
        json_data['prices'] = prices[item.id].to_dict()
        output.append(json_data)
    return JSONResponse(output)
