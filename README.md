
***Deprecated and no longer updated, use [photoSync](https://github.com/soCzech/photoSync) instead.***

___


flickrSync
==========
Python Flickr photo synchronization using OAuth

- OAuth sign in
- Download photos to local folders accoding to the Flickr albums
- Upload local photos which haven't been yet uploaded to respective albums
- Delete photos which are not present on your hard drive
- Synchronize all your Flickr photos with your local folder (both ways)

Installation
------------
1. In **flickSync/\_\_init\_\_.py** set:
    - **\_\_logLevel\_\_** to 10, 20, 40 or 50 in order to see DEBUG, INFO, WARNING, ERROR or CRITICAL messages in log file
    - **\_\_exclude\_\_** to list of folders which should be ignored (thumbs etc.)
    - **\_\_callback\_\_** to URL which is called when OAuth verifier requested
    - You can also set key and secret if you want to use your own app [(get a key)](https://www.flickr.com/services/apps/create/apply/)

2. Install the package

        $ python setup.py install

Requires [**requests** library](https://github.com/kennethreitz/requests/) and **Python v3.+**

Usage
-----
***Don't worry, this package as it is CANNOT delete your local photos. But it CAN delete your photos uploded to Flickr. Keep that in mind before you recklessly try it.***

For the most common usage is the **app.py** file located in the **bin** folder. This script can synchronize all your photos from particular folder (and its subfolders) to Flickr. You can choose if you want to upload photos only, download them only, or if you want to combine upload, download or even deletion to truly sync the photos.

    $ python /path/to/app.py -f "/path/to/photo/folder/" -s -d -u
    #	-s (downloads all the photos which are not in /path/to/photo/folder/ from Flickr)
    #	-d (DELETES ALL THE PHOTOS which are not in /path/to/photo/folder/ from Flickr)
    #	-u (uploads all the photos which are not on Flickr from /path/to/photo/folder/)


You don't need to modify the app.py file. All you need is to use any command similar to the one in **run.sh** file in **bin** folder or you can schedule periodical inicialization (in case you forget to sync it manually).

Documentation
-------------
***Sorry, work in progress :(***
