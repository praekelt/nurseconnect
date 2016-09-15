from django.template import Library

from molo.core.templatetags.core_tags import get_pages

register = Library()


@register.inclusion_tag('core/tags/footerlink.html', takes_context=True)
def footer_link(context):
    request = context['request']
    locale = context.get('locale_code')

    if request.site:
        pages = request.site.root_page.specific.footers()
    else:
        pages = []

    return {
        'footers': get_pages(context, pages, locale),
        'request': context['request'],
        'locale_code': locale,
    }
