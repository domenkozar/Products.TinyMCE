"""
Based on "TinyMCE Compressor PHP" from MoxieCode.

http://tinymce.moxiecode.com/

Copyright (c) 2008 Jason Davies
Licensed under the terms of the MIT License (see LICENSE.txt)
"""

from Acquisition import aq_inner
from datetime import datetime
import os.path

from zope.component import queryUtility, getMultiAdapter
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.ResourceRegistries.tools.packer import JavascriptPacker

from Products.TinyMCE.interfaces.utility import ITinyMCE
from Products.CMFCore.utils import getToolByName

try:
    import simplejson as json
    json  # Pyflakes
except ImportError:
    import json

def isContextUrl(url):
    """Some url do not represent context. Check is based on url. If 
    fragment are detected, this method return False
    fragments are portal_factory, ++contextportlets++, ++groupportlets++,
    ++contenttypeportlets++
    """
    fragments = ('portal_factory', '++contextportlets++', '++groupportlets++', 
                '++contenttypeportlets++')

    for fragment in fragments:
        if fragment in url:
            return False

    return True

class TinyMCECompressorView(BrowserView):
    tiny_mce_gzip = ViewPageTemplateFile('tiny_mce_gzip.js')

    # TODO: cache
    def __call__(self):
        plugins = self.request.get("plugins", "").split(',')
        languages = self.request.get("languages", "").split(',')
        themes = self.request.get("themes", "").split(',')
        isJS = self.request.get("js", "") == "true"
        suffix = self.request.get("suffix", "") == "_src" and "_src" or ""
        response = self.request.response
        response.setHeader('Content-type', 'application/javascript')
        base_url = '/'.join([self.context.absolute_url(), self.__name__])
        # fix for Plone <4.1 http://dev.plone.org/plone/changeset/48436
        # only portal_factory part of condition!
        if not isContextUrl(base_url):
            portal_state = getMultiAdapter((self.context, self.request),
			    name="plone_portal_state")
            base_url = '/'.join([portal_state.portal_url(), self.__name__])

        if not isJS:
            tinymce_config = []
            if not hasattr(self.context, 'schema'):
                return ''
            for field in self.context.schema.filterFields(type='text'):
                if field.widget.getName() == 'RichWidget':
                    fieldname = field.getName()
                    jsonconfig = getMultiAdapter((self.context, self.request),
                                             name="tinymce-jsonconfiguration")
                    tinymce_config.append({'fieldname': fieldname,
                                           'config': jsonconfig(fieldname, base_url)})
            tiny_mce_gzip = self.tiny_mce_gzip(tinymce_json_config=tinymce_config)
            js_tool = getToolByName(aq_inner(self.context), 'portal_javascripts')
            if js_tool.getDebugMode():
                return tiny_mce_gzip
            else:
                return JavascriptPacker('safe').pack(tiny_mce_gzip)

        now = datetime.utcnow()
        response['Date'] = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

        traverse = lambda name: str(self.context.restrictedTraverse(name, ''))

        # Add core, with baseURL added
        content = [
            traverse("tiny_mce%s.js" % suffix).replace(
                "tinymce._init();",
                "tinymce.baseURL='%s';tinymce._init();" % base_url)
        ]

        # add custom plugins
        portal_tinymce = getToolByName(self.context,'portal_tinymce')
        customplugins = {}
        for plugin in portal_tinymce.customplugins.splitlines():
            if '|' in plugin:
                name, path = plugin.split('|', 1)
                customplugins[name] = path

                content.append('tinymce.PluginManager.load("%s", "%s/%s");' % (
                    name, config['portal_url'], path));

        # Add core languages
        # TODO: we have our own translations
        for lang in languages:
            content.append(traverse("langs/%s.js" % lang))

        # Add themes
        for theme in themes:
            content.append(traverse("themes/%s/editor_template%s.js" % (theme, suffix)))

            for lang in languages:
                content.append(traverse("themes/%s/langs/%s.js" % (theme, lang)))

        # Add plugins
        for plugin in plugins:
            if plugin in customplugins:
                script = customplugins[plugin]
                path, bn = os.path.split(customplugins[plugin])
            else:
                script = "plugins/%s/editor_plugin%s.js" % (plugin, suffix)
                path = 'plugins/%s' % plugin

            content.append(traverse(script))

            for lang in languages:
                content.append(traverse("%s/langs/%s.js" % (path, lang)))

        # TODO: add aditional javascripts in plugins

        return ''.join(content)
