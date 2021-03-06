'''
    Copyright (C) 2017 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''

import json

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.utils.encoding import force_text
from django.utils.functional import Promise

from perftools.models import JSONStore
from retail.utils import build_stat_results, programming_languages


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        if isinstance(obj, QuerySet):
            if obj.count() and type(obj.first()) == str:
                return obj[::1]
            return [model_to_dict(instance) for instance in obj]
        return super(LazyEncoder, self).default(obj)


class Command(BaseCommand):

    help = 'generates some /results data'

    def handle(self, *args, **options):
        keywords = [''] + programming_languages
        # DEBUG OPTIONS
        # keywords = [''] 
        view = 'results'
        with transaction.atomic():
            items = []
            JSONStore.objects.filter(view=view).all().delete()
            for keyword in keywords:
                key = keyword
                print(f"- executing {keyword}")
                data = build_stat_results(keyword)
                print("- creating")
                items.append(JSONStore(
                    view=view,
                    key=key,
                    data=json.loads(json.dumps(data, cls=LazyEncoder)),
                    ))
        JSONStore.objects.bulk_create(items)
