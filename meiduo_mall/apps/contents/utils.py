from collections import OrderedDict

from apps.goods.models import GoodsChannel


def get_categories():
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    categories = OrderedDict()
    for channel in channels:
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        cat1 = channel.category
        # categories[group_id]['channels'].append({
        #     'id': cat1.id,
        #     'name': cat1.name,
        #     'url': channel.url
        # })
        cat1.url = channel.url
        categories[group_id]['channels'].append(cat1)

        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)
    return categories