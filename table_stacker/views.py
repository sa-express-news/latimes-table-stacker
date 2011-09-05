# Response helpers
import os
import csv
from django.shortcuts import render, get_object_or_404
from django.utils import simplejson
from django.http import Http404, HttpResponse, HttpResponseRedirect

# Models
from table_stacker.models import Table, Tag

# Pagination
from django.core.paginator import Paginator
from django.core.paginator import  InvalidPage, EmptyPage

# Cache
from django.conf import settings


#
# The biz
#

def get_table_page(request, page):
    """
    Creates a page of tables for our index and pagination system.
    """
    # Pull the data
    qs = Table.live.all()
    paginator = Paginator(qs, 10)
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        raise Http404
    # Create a response and pass it back
    context = {
        'headline': 'Latest spreadsheets',
        'object_list': page.object_list,
        'page_number': page.number,
        'has_next': page.has_next(),
        'next_page_number': page.next_page_number(),
    }
    return render(request, 'table_list.html', context)


def table_index(request):
    """
    A list of all the public tables
    """
    return get_table_page(request, 1)


def table_page(request, page):
    """
    A page of documents as we leaf back through everything in reverse chron.
    """
    # Send /page/1/ back to the index url
    if page == '1':
        return HttpResponseRedirect('/')
    return get_table_page(request, page)


def tag_page(request, tag, page):
    """
    Lists tables with a certain tag.
    """
    tag = get_object_or_404(Tag, slug=tag)
    object_list = tag.table_set.live()
    paginator = Paginator(object_list, 10)
    # Limit it to thise page
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        raise Http404
    # Create a response and pass it back
    context = {
        'headline': 'Spreadsheets tagged &lsquo;%s&rsquo;' % tag.title,
        'object_list': page.object_list,
        'page_number': page.number,
        'has_next': page.has_next(),
        'next_page_number': page.next_page_number(),
        'object': tag,
    }
    return render(request, 'table_list.html', context)


def table_detail(request, slug):
    """
    A detail page all about one of the tables.
    """
    obj = get_object_or_404(Table, slug=slug)
    if not obj.is_published:
        raise Http404
    context = {
        'object': obj,
        'table': obj.get_tablefu(),
        'size_choices': [1,2,3,4],
    }
    return render(request, 'table_detail.html', context)


def table_xls(request, slug):
    """
    A table, in Excel format.
    
    Lifted from http://www.djangosnippets.org/snippets/911/
    """
    # Get the csv data
    obj = get_object_or_404(Table, slug=slug)
    if not obj.is_published:
        raise Http404
    csv_path = os.path.join(settings.CSV_DIR, obj.csv_name)
    csv_data = open(csv_path, 'r').read()
    context = {'csv': unicode(csv_data)}
    # Prep an XLS response
    response = render(request, "table.xls.txt", context)
    response['Content-Disposition'] = 'attachment; filename=%s.xls' % slug
    response['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    return response


def table_json(request, slug):
    """
    A table, in json format.
    """
    # Get the csv data
    obj = get_object_or_404(Table, slug=slug)
    if not obj.is_published:
        raise Http404
    csv_path = os.path.join(settings.CSV_DIR, obj.csv_name)
    csv_data = list(csv.reader(open(csv_path, 'r')))
    # Convert it to JSON key/value formatting
    headers = csv_data.pop(0)
    dict_list = []
    for row in csv_data:
        col_dict = {}
        for i, h in enumerate(headers):
            col_dict[h] = row[i]
        dict_list.append(col_dict)
    # Pass it out
    return HttpResponse(simplejson.dumps(dict_list), mimetype="text/javascript")


def sitemap(request):
    """
    Create a sitemap.xml file for Google and other search engines.
    """
    table_list = Table.live.all()
    tag_list = Tag.objects.all()
    context = {
        'tag_list': tag_list,
        'table_list': table_list,
    }
    response = render(request, 'sitemap.xml', context)
    response.mimetype='text/xml'
    return response


