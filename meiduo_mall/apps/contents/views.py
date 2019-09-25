
from django.shortcuts import render
from django.views import View

from apps.contents.models import ContentCategory
from apps.contents.utils import get_categories


class IndexView(View):
    def get(self, request):
        categories = get_categories()
        contents={}
        ad_categories = ContentCategory.objects.all()
        for ad_cat in ad_categories:
            contents[ad_cat.key] = ad_cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': {},
            'contents': contents
        }

        return render(request, 'index.html', context)
