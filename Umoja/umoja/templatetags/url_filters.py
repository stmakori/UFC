from django import template
from urllib.parse import urlencode, parse_qs, urlparse, urlunparse

register = template.Library()

@register.filter
def remove_param(url_string, param_name):
    """
    Remove a parameter from a URL query string.
    Usage: {{ request.GET.urlencode|remove_param:"key" }}
    """
    if not url_string:
        return ''
    
    # Parse the query string
    params = parse_qs(url_string)
    
    # Remove the specified parameter
    if param_name in params:
        del params[param_name]
    
    # Rebuild the query string
    return urlencode(params, doseq=True)

@register.filter
def update_page(url_string, page_number):
    """
    Update the page parameter in a URL query string.
    Usage: {{ request.GET.urlencode|update_page:1 }}
    """
    if not url_string:
        return f'page={page_number}'
    
    # Parse the query string
    params = parse_qs(url_string)
    
    # Update the page parameter
    params['page'] = [str(page_number)]
    
    # Rebuild the query string
    return urlencode(params, doseq=True)

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
