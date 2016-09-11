import functools
import json

import six
from bs4 import BeautifulSoup

from .storage import PageHistory


def pipeline_factory(conf):
    rules = conf.get('transform', [])
    if isinstance(rules, six.string_types):
        rules = [rules]
    return functools.partial(
        pipeline,
        transformers=[
            transformer_factory(conf, rule)
            for rule in rules
        ]
    )


def pipeline(ok, content, transformers):
    for transformer in transformers:
        if ok:
            ok, content = transformer(content)
        else:
            break
    return ok, content


def transformer_factory(conf, rule):
    try:
        name, value = next(iter(rule.items()))
    except AttributeError:
        name, value = rule, None
    if name == 'css':
        return functools.partial(css_selector, value)
    elif name == 'tag':
        return functools.partial(tag_selector, value)
    elif name == 'text':
        return extract_text
    elif name == 'changes':
        return PageHistory(conf).report_changes
    elif name == 'json':
        return pretty_json
    else:
        raise RuntimeError(
            "Unknown transformer: %r" % (name,)
        )


def pretty_json(text):
    return True, json.dumps(
        json.loads(text),
        indent=True,
        sort_keys=True,
        ensure_ascii=False,
        # encoding='utf-8',
    )


def tag_selector(name, html):
    soup = BeautifulSoup(html, "html.parser")
    element = soup.find(name)
    if element:
        return True, six.text_type(element)
    else:
        return False, html


def css_selector(selector, html):
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(selector)
    if element:
        return True, six.text_type(element)
    else:
        return False, html


def extract_text(html):
    strings = BeautifulSoup(html, "html.parser").stripped_strings
    return True, u'\n'.join([
        line
        for line in strings
        if line
    ])