import sublime
import sublime_plugin
import threading
import base64
import os
import re
import urllib.request

# Thanks Leonid Shevtsov https://github.com/leonid-shevtsov/ClickableUrls_SublimeText
class RemoteImagesPreview(sublime_plugin.EventListener):

    # Thanks Jeff Atwood http://www.codinghorror.com/blog/2008/10/the-problem-with-urls.html
    # ^ that up here is a URL that should be matched
    URL_REGEX = "\\bhttps?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;']*[-A-Za-z0-9+&@#/%=~_(|]\.(?:jpg|gif|png)"
    DATA_URI_REGEX = "\\bdata:image/[\w\/\+]+;(charset=[\w-]+|base64).*,(.*)\\b"
    RELATIVE_PATH_REGEX = "[-A-Za-z0-9+&@#/%?~_|!:,.;]*[-A-Za-z0-9+&@#/%=~_(|]\.(?:jpg|gif|png)"

    DEFAULT_MAX_URLS = 200
    SETTINGS_FILENAME = 'RemoteImagesPreview.sublime-settings'

    images_for_view = {}
    scopes_for_view = {}
    ignored_views = []
    highlight_semaphore = threading.Semaphore()

    def on_activated(self, view):
        self.update_url_highlights(view)

    # Blocking handlers for ST2
    def on_load(self, view):
        if sublime.version() < '3000':
            self.update_url_highlights(view)

    def on_modified(self, view):
        if sublime.version() < '3000':
            self.update_url_highlights(view)

    # Async listeners for ST3
    def on_load_async(self, view):
        self.update_url_highlights_async(view)

    def on_modified_async(self, view):
        self.update_url_highlights_async(view)

    def on_close(self, view):
        for map in [self.images_for_view, self.scopes_for_view, self.ignored_views]:
            if view.id() in map:
                del map[view.id()]

    """The logic entry point. Find all URLs in view, store and highlight them"""
    def update_url_highlights(self, view):

        settings = sublime.load_settings(RemoteImagesPreview.SETTINGS_FILENAME)
        should_highlight_images = settings.get('highlight_images', True)
        max_url_limit = settings.get('max_url_limit', RemoteImagesPreview.DEFAULT_MAX_URLS)

        if view.id() in RemoteImagesPreview.ignored_views:
            return

        urls = view.find_all(RemoteImagesPreview.URL_REGEX)
        data_uris = view.find_all(RemoteImagesPreview.DATA_URI_REGEX)
        relative_paths = view.find_all(RemoteImagesPreview.RELATIVE_PATH_REGEX)

        # Avoid slowdowns for views with too much URLs
        if len(urls) + len(data_uris) > max_url_limit:
            print("RemoteImagesPreview: ignoring view with %u URLs" % len(urls))
            RemoteImagesPreview.ignored_views.append(view.id())
            return

        RemoteImagesPreview.images_for_view[view.id()] = {
            'urls': urls,
            'data_uris': data_uris,
            'relative_paths': relative_paths,
        }

        should_highlight_images = sublime.load_settings(RemoteImagesPreview.SETTINGS_FILENAME).get('highlight_images', True)
        if (should_highlight_images):
            self.highlight_images(view, urls + data_uris + relative_paths)

    """Same as update_url_highlights, but avoids race conditions with a
    semaphore."""
    def update_url_highlights_async(self, view):
        RemoteImagesPreview.highlight_semaphore.acquire()
        try:
            self.update_url_highlights(view)
        finally:
            RemoteImagesPreview.highlight_semaphore.release()

    """Creates a set of regions from the intersection of urls and scopes,
    underlines all of them."""
    def highlight_images(self, view, urls):
        # We need separate regions for each lexical scope for ST to use a proper color for the underline
        scope_map = {}
        for url in urls:
            scope_name = view.scope_name(url.a)
            scope_map.setdefault(scope_name, []).append(url)

        for scope_name in scope_map:
            self.underline_regions(view, scope_name, scope_map[scope_name])

        self.update_view_scopes(view, scope_map.keys())

    """Apply underlining with provided scope name to provided regions.
    Uses the empty region underline hack for Sublime Text 2 and native
    underlining for Sublime Text 3."""
    def underline_regions(self, view, scope_name, regions):
        if sublime.version() >= '3019':
            # in Sublime Text 3, the regions are just underlined
            view.add_regions(
                u'remote-images-preview ' + scope_name,
                regions,
                scope_name,
                flags=sublime.DRAW_NO_FILL|sublime.DRAW_NO_OUTLINE|sublime.DRAW_STIPPLED_UNDERLINE)
        else:
            # in Sublime Text 2, the 'empty region underline' hack is used
            char_regions = [sublime.Region(pos, pos) for region in regions for pos in range(region.a, region.b)]
            view.add_regions(
                u'remote-images-preview ' + scope_name,
                char_regions,
                scope_name,
                sublime.DRAW_EMPTY_AS_OVERWRITE)

    """Store new set of underlined scopes for view. Erase underlining from
    scopes that were used but are not anymore."""
    def update_view_scopes(self, view, new_scopes):
        old_scopes = RemoteImagesPreview.scopes_for_view.get(view.id(), None)
        if old_scopes:
            unused_scopes = set(old_scopes) - set(new_scopes)
            for unused_scope_name in unused_scopes:
                view.erase_regions(u'remote-images-preview ' + unused_scope_name)

        RemoteImagesPreview.scopes_for_view[view.id()] = new_scopes

    def on_hover(self, view, point, hover_zone):
        if (hover_zone == sublime.HOVER_TEXT):
            if view.id() in RemoteImagesPreview.images_for_view:
                hover = next((url for url in RemoteImagesPreview.images_for_view[view.id()]['urls'] if url.contains(point)), None)
                if hover:
                    url = view.substr(hover)
                    image = urllib.request.urlopen(url).read()
                    encoded = str(base64.b64encode(image), "utf-8")
                    view.show_popup(
                        '<img src="data:image/png;base64,' + encoded + '">',
                        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                        location=point, max_width=1000, max_height=1000
                    )
                    return

                hover = next((data_uri for data_uri in RemoteImagesPreview.images_for_view[view.id()]['data_uris'] if data_uri.contains(point)), None)
                if hover:
                    data_uri = view.substr(hover)
                    view.show_popup(
                        '<img src="' + data_uri + '">',
                        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                        location=point, max_width=1000, max_height=1000
                    )
                    return

                hover = next((data_uri for data_uri in RemoteImagesPreview.images_for_view[view.id()]['relative_paths'] if data_uri.contains(point)), None)
                if hover:

                    relative_path = view.substr(hover)

                    current_file = view.file_name()
                    current_path = os.path.dirname(current_file)

                    file_name = current_path + '/' + relative_path

                    # Check that file exists
                    if (file_name and os.path.isfile(file_name)):
                        encoded = str(base64.b64encode(
                            open(file_name, "rb").read()
                        ), "utf-8")

                        view.show_popup(
                            '<img src="data:image/png;base64,' + encoded + '">',
                            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                            location=point, max_width=1000, max_height=1000
                        )

        return
