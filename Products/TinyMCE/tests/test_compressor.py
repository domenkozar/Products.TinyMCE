# -*- coding: utf-8 -*-

from Products.TinyMCE.browser.compressor import TinyMCECompressorView
from Products.TinyMCE.tests.base import IntegrationTestCase


class ViewTestCase(IntegrationTestCase):

    def setUp(self):
        super(ViewTestCase, self).setUp()
        self.portal.invokeFactory('Folder', 'foobar')

    def test_compressorview_basic(self):
        view = TinyMCECompressorView(self.portal.foobar, self.portal.REQUEST)
        view.__name__ = 'tiny_mce_gzip.js'
        self.assertTrue(view().startswith(
            "jQuery(function($){"))

    def test_compressorview_customplugins(self):
        self.portal.foobar.REQUEST['js'] = 'true'
        self.portal.portal_tinymce.customplugins = u"plonebrowser\nplonelink|path\nploneimage"
        view = TinyMCECompressorView(self.portal.foobar, self.portal.REQUEST)
        view.__name__ = 'tiny_mce_gzip.js'
        self.assertIn('plonelink', view())

    def test_compressorview_dexterity(self):
        pass  # TODO

    def test_compressorview_multiple_widgets(self):
        pass  # TODO
