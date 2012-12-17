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

def invention(request, item_id, item_slug):
    item = Item.objects.get(id=item_id)
    if item.invention_chance == 0:
        return TemplateResponse(request, 'bad_item.html', {'item': item})
    skills = [req.skill for req in item.blueprint.invention_requirements]
    encryption_skill = [s for s in skills if 'Encryption Methods' in s][0]
    skills.remove(encryption_skill)
    skills.sort()
    return TemplateResponse(request, 'item.html', {
        'item': item,
        'invention_data': {
            'baseInventionChance': item.invention_chance,
            'encryptionSkill': encryption_skill,
            'coreSkill1': skills[0],
            'coreSkill2': skills[1],
            'metas': [m.item_id for m in ItemMeta.objects.filter(parent=item, meta_group_id=1)],
            'requirements': item.blueprint.invention_requirements,
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
