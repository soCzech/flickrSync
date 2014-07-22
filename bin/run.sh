# run app.py
#	-f (set folder to "/path/to/photo/folder/") ! mandatory
#	-s (download files which are not in /path/to/photo/folder/ from Flickr)
#	-d (delete files which are not in /path/to/photo/folder/ from Flickr)
#	-u (upload files which are not on Flickr from /path/to/photo/folder/)
#	-m (upload only 100 files at once)
#	-w (wait 1 seconds between uploads)
python /path/to/app.py -f "/path/to/photo/folder/" -s -d -u -m 100 -w 1