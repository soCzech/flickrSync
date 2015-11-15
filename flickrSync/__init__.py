__ver__ = "0.6.0"
__app__ = "flickrSync " + __ver__
__key__ = "0a178c1bac385f683a20e2e8ddd484d5"
__secret__ = "f492dba3ec10000f"

__exclude__ = ["@eaDir"]
__logFile__ = "flickr.info.log"
__commFile__ = "flickr.communication.log"
__logLevel__ = 10 # DEBUG: 10; INFO: 20; WARNING: 30; ERROR: 40; CRITICAL: 50
__consoleLevel__ = 10
__callback__ = "http://www.example.com"

from .flickrapi import FlickrAPI
