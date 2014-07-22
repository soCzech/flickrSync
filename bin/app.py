import sys
import os.path
import argparse
from flickrSync import FlickrAPI

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-a", "--authorize", action="store_true", help="run the authorization setup")
	parser.add_argument("-f", "--folder", action="store", help="folder to synchronize")
	parser.add_argument("-d", "--deletion", action="store_true", help="allow deletion on Flickr while synchronizing")
	parser.add_argument("-s", "--saving", action="store_true", help="allow download from Flickr while synchronizing")
	parser.add_argument("-u", "--upload", action="store_true", help="allow upload to Flickr while synchronizing")
	parser.add_argument("-m", "--max", action="store", help="maximal number of downloads / uploads at once (0 means unlimited)")
	parser.add_argument("-w", "--wait", action="store", help="time to wait between downloads / uploads")
	args = parser.parse_args()

	LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
	
	if not args.wait:
		args.wait = 0;
	else:
		args.wait = float(args.wait)
	if not args.max or float(args.max) == 0:
		args.max = False;
	else:
		args.max = int(float(args.max))
	
	if args.folder or args.authorize:
		INSTANCE = FlickrAPI(LOCAL_DIR)

		authorized = INSTANCE.CheckTokens()
		if args.authorize and not authorized:
			authorized = INSTANCE.OAuthSingIn()
		if authorized and args.folder:
			INSTANCE.SyncPhotos(args.folder, args.saving, args.deletion, args.upload, args.max, args.wait)
	else:
		parser.print_help()