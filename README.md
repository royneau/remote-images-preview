# Remote Images Preview
Sublime Text Plugin for previewing remote images.

A plugin for [Sublime Text 2 and 3](http://sublimetext.com)

## Summary

This plugin underlines remote image URLs in Sublime Text, and lets you preview the images simply by hovering on their URLs.

**Performance warning.** The plugin is automatically disabled if the document has more than 200 remote image URLs, in order to avoid a massive performance hit. To change this number, set the `max_url_limit` option (see "Configuration" below). 

## Installation

_macOS_
```
cd ~/Library/Application\ Support/Sublime\ Text\ 3/Packages
git clone --depth=1 https://github.com/royneau/remote-images-preview.git
```

_Ubuntu_
```
cd ~/.config/sublime-text-3/Packages
git clone --depth=1 https://github.com/royneau/remote-images-preview.git
```

_Windows_
```
cd "%APPDATA%\Sublime Text 3\Packages"
git clone --depth=1 https://github.com/royneau/remote-images-preview.git
```

Or manually create a folder named "remote-images-preview" on your Sublime Text's Packages folder and copy the content of this repo to it.

## Configuration

All configuration is done via the settings file that you can open via the main menu: `Preferences > Package Settings > Remote Images Preview > Settings - User`.

### Disabling URL highlighting

Unfortunately, the only way to underline a block of text in Sublime Text 2 is a hack with underlining empty regions, and there is no way to control its appearance. If you want, you can disable URL highlighting by setting the option `highlight_images` to false.

    {
        "highlight_images": false
    }

Note that this isn't an issue with Sublime Text 3.

## Known Issues

* URLs are not underlined in Markdown files when using the [MarkdownEditing plugin](https://github.com/SublimeText-Markdown/MarkdownEditing) plugin (that plugin applies its own styles to the URLs). Otherwise RemoteImagesPreview works as usual.

* * *

(c) 2017 [royneau](https://github.com/royneau) under the MIT license.
