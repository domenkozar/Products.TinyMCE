from zope.interface import implements
try:
    import simplejson as json
    json   # pyflakes
except ImportError:
    import json

from Products.TinyMCE.adapters.interfaces.JSONSearch import IJSONSearch


class JSONSearch(object):
    """Returns a list of search results in JSON"""
    implements(IJSONSearch)

    def __init__(self, context):
        """Constructor"""
        self.context = context

    def getSearchResults(self, filter_portal_types, searchtext):
        """Returns the actual search result"""

        catalog_results = []
        results = {}
        query = {}
        query['portal_type'] = filter_portal_types
        query['sort_on'] = 'sortable_title'
        query['path'] = self.context.absolute_url_path()
        #query['SearchableText'] = searchtext
        #weird , need to cleanup searchable text
        query['SearchableText'] = searchtext.replace('%20', ' ')
        
        results['parent_url'] = ''
        results['path'] = []
        if searchtext:
            plone_layout = self.context.restrictedTraverse('@@plone_layout', 
                                                           None)
            if plone_layout is None:
                # Plone 3
                plone_view = self.context.restrictedTraverse('@@plone')
                getIcon = lambda brain: plone_view.getIcon(brain).html_tag()
            else:
                # Plone >= 4
                getIcon = lambda brain: plone_layout.getIcon(brain)()
            
            brains = self.context.portal_catalog.searchResults(**query)

            for brain in brains:
                catalog_results.append({
                    'id': brain.getId,
                    'uid': brain.UID,
                    'url': brain.getURL(),
                    'portal_type': brain.portal_type,
                    'title': brain.Title == "" and brain.id or brain.Title,
                    'icon': getIcon(brain),
                    'description': brain.Description,
                    'is_folderish': brain.is_folderish,
                    })

        # add catalog_results
        results['items'] = catalog_results

        # never allow upload from search results page
        results['upload_allowed'] = False

        # return results in JSON format
        self.context.REQUEST.response.setHeader("Content-type",
                                                "application/json")
        return json.dumps(results)
