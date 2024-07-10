from django.shortcuts import render
from django.urls import get_resolver, URLPattern, URLResolver


def list_urls(urlconf, namespace=None, prefix=''):
    urls = []
    for entry in urlconf:
        if isinstance(entry, URLPattern):
            urls.append((namespace, prefix + str(entry.pattern)))
        elif isinstance(entry, URLResolver):
            new_namespace = f"{namespace}:{entry.namespace}" if namespace else entry.namespace
            urls.extend(list_urls(entry.url_patterns, new_namespace, prefix + str(entry.pattern)))
    return urls


def endpoints(request):
    urlconf = get_resolver().url_patterns
    all_urls = list_urls(urlconf)

    app_urls = {}
    media_urls = []
    static_urls = []

    for namespace, url in all_urls:
        if 'media' in url:
            media_urls.append(url)
        elif 'static' in url:
            static_urls.append(url)
        else:
            app_name = namespace.split(':')[0] if namespace else 'root'
            if app_name not in app_urls:
                app_urls[app_name] = []
            app_urls[app_name].append(url)

    context = {
        'app_urls': app_urls,
        'media_urls': media_urls,
        'static_urls': static_urls,
    }

    return render(request, 'endpoints/endpoints.html', context)
