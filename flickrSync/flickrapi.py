import os
import re
import sys
import logging
import webbrowser

from time import sleep
from inspect import stack
from urllib.request import urlopen, unquote

from .helper import path_to_array
from .flickrhandler import FlickrHandler
from . import __app__, __callback__, __exclude__, __logFile__, __logLevel__


data_file = "flickr.session.dat"

base = "https://api.flickr.com/services"
rest = base + "/rest"
upload = base + "/upload"
auth_rt = base + "/oauth/request_token"
auth_at = base + "/oauth/access_token"

logging.basicConfig(format = "%(levelname)s / %(funcName)s: \t%(message)s @ line %(lineno)d", \
	filename = __logFile__, filemode="w", level = __logLevel__)
log = logging.getLogger("FlickrAPI")


class FlickrAPI():
	def __init__(self, directory):
		log.info(__app__ + "\n" + len(__app__) * "-")
		self.DIR = directory
		self.API = FlickrHandler(self.DIR)

	"""
		OAuth
	"""

	def CheckTokens(self):
		log.debug("Running...")
		try:
			file = open(os.path.join(self.DIR, data_file), mode="r", encoding=sys.getfilesystemencoding()) #????
			lines = tuple(file)
			file.close()
			for l in lines:
				l = l.strip().split("=")
				if l[0] == "oauth_token": self.API.TOKEN = l[1].strip()
				elif l[0] == "oauth_token_secret": self.API.TOKEN_SECRET = l[1].strip()
			if not self.API.TOKEN or not self.API.TOKEN_SECRET:
				self.API.TOKEN = ""
				self.API.TOKEN_SECRET = ""
		except Exception as e:
			log.exception(e)
		finally:
			if not self.API.TOKEN:
				log.info("OAuth needed before using the synchronization.")
				return False
			else:
				log.debug("OAuth tokens look good, you can proceed.")
				return True

	def OAuthSingIn(self):
		log.debug("Running...")
		try:
			os.remove(os.path.join(self.DIR, data_file))
		except:
			pass

		resp_token = self.API.send_get(auth_rt, {
			"oauth_callback": __callback__
		})

		if resp_token["stat"] == "ok":
			self.API.TOKEN = resp_token["oauth_token"]
			self.API.TOKEN_SECRET = resp_token["oauth_token_secret"]

			url = base + "/oauth/authorize?oauth_token=" + self.API.TOKEN
			webbrowser.open(url)

			print("Authorize the app in browser using this URL\n\t" + url)
			print("Enter your oauth_verifier from callback URL")

			verifier = input("~~~")
			if verifier != "":

				resp_verifier = self.API.send_get(auth_at, {
					"oauth_verifier": verifier,
					"oauth_token": self.API.TOKEN
				})

				if resp_verifier["stat"] == "ok":
					self.API.TOKEN = resp_verifier["oauth_token"]
					self.API.TOKEN_SECRET = resp_verifier["oauth_token_secret"]

					session = open(os.path.join(self.DIR, data_file), "w+")
					session.write("fullname=" + unquote(resp_verifier["fullname"]) \
						+ "\noauth_token=" + self.API.TOKEN \
						+ "\noauth_token_secret=" + self.API.TOKEN_SECRET \
						+ "\nuser_nsid=" + unquote(resp_verifier["user_nsid"]) \
						+ "\nusername=" + resp_verifier["username"])
					session.close()

					log.info("Signed in as %s", unquote(resp_verifier["fullname"]))
					return True

		log.critical("Something unexpected happened, try the authorization again.")
		return False

	"""
		Individual photo functions
	"""

	def AddPhotoToAlbum(self, photo_id, album_id):
		log.debug("Adding photo %s to album %s.", str(photo_id), str(album_id))
		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.addPhoto",
			"format": "json",
			"nojsoncallback": 1,
			"photo_id": photo_id,
			"photoset_id": album_id
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			log.debug("Photo %s added to album %s.", str(photo_id), str(album_id))
			return True

		log.error("Photo %s couldn't be added to album %s.", str(photo_id), str(album_id))
		return False

	def DeletePhoto(self, photo_id):
		log.debug("Deleting photo %s.", str(photo_id))
		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photos.delete",
			"photo_id": photo_id,
			"format": "json",
			"nojsoncallback": 1
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			log.debug("Photo %s deleted.", str(photo_id))
			return True

		log.error("Photo %s couldn't be deleted.", str(photo_id))
		return False

	def DownloadPhoto(self, photo, directory):
		log.debug("Downloading photo %s to %s.", photo["title"], directory)

		title = photo["title"]
		if re.match("(?:.*)(jpg)$", photo["title"], re.IGNORECASE) == None:
			title += "." + photo["originalformat"]
		try:
			url = "https://farm%s.staticflickr.com/%s/%s_%s_o.%s" \
				% (photo["farm"], photo["server"], photo["id"], photo["originalsecret"], photo["originalformat"])
			file = urlopen(url)
			output = open(os.path.join(directory, title), "wb")
			output.write(file.read())
			output.close()
			log.debug("Photo %s downloaded.", photo["title"])
			return True
		except:
			pass
		log.error("Photo %s couldn't be downloaded to %s.", photo["title"], directory)
		return False

	def UploadPhoto(self, file, data):
		log.debug("Uploading photo %s.", file)

		parameters = {
			"oauth_token": self.API.TOKEN,
			"title": file,
			"description": "",
			"tags": "",
			"is_public": 0,
			"is_friend": 0,
			"is_family": 0,
			"safety_level": 1,
			"content_type": 1,
			"hidden": 2
		}
		parameters.update(data)

		resp = self.API.send_file(upload, parameters, file)

		if resp["stat"] == "ok":
			log.debug("Photo %s uploaded.", data["title"])
			return resp["photoid"]["text"]

		log.error("Photo %s couldn't be uploaded.", file)
		return False

	"""
		Album functions
	"""

	def CreateAlbum(self, name, primary_photo_id, description):
		log.debug("Creating album %s.", name)

		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.create",
			"format": "json",
			"nojsoncallback": 1,
			"title": name,
			"primary_photo_id": primary_photo_id,
			"description": (description if description else "")
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			log.debug("Album %s created.", name)
			return resp["photoset"]["id"]

		log.error("Album %s couldn't be created.", name)
		return False

	def GetAlbums(self):
		log.debug("Running...")
		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.getList",
			"format": "json",
			"nojsoncallback": 1,
			"page": 1
		}

		(albums, no_of_pages) = ({}, 1)
		while parameters["page"] <= no_of_pages:
			resp = self.API.send_post(rest, parameters)

			if resp["stat"] == "ok":
				no_of_pages = resp["photosets"]["pages"]
				for album in resp["photosets"]["photoset"]:
					albums[album["title"]["_content"]] = album["id"]
			else:
				log.error("Albums couldn't be retrieved.")
				return False
			parameters["page"] += 1

		log.debug("All albums retrieved.")
		return albums

	def GetPhotosInAlbum(self, album_id, album_name):
		log.debug("Getting photos in %s.", album_name)

		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.getPhotos",
			"format": "json",
			"nojsoncallback": 1,
			"photoset_id": album_id,
			"extras": "original_format",
			"page": 1
		}

		(photos, photos_short, no_of_pages) = ([], [], 1)
		while parameters["page"] <= no_of_pages:
			resp = self.API.send_post(rest, parameters)

			if resp["stat"] == "ok":
				no_of_pages = resp["photoset"]["pages"]
				for photo in resp["photoset"]["photo"]:
					photo["album"] = album_name
					photos_short.append([photo["album"], photo["title"]])
					photos.append(photo)
			else:
				log.error("Photos in %s couldn't be retrieved.", album_name)
				return False
			parameters["page"] += 1

		log.debug("Photos in %s retrieved.", album_name)
		return (photos, photos_short)

	"""
		Synchronization functions
	"""

	def GetPhotosInDirectory(self, directory):
		log.debug("Running...")
		photos = []
		subdir = len(path_to_array(directory))

		for root, dirs, files in os.walk(directory):
			for file in files:
				ext = file.lower().split(".")[-1]
				if (ext == "jpg"):
					safe = True
					to_remove = []
					file_path = path_to_array(root)[subdir:]

					for path in __exclude__:
						if path in file_path:
							safe = False
					for path in file_path:
						if path[:2] == "__":
							safe = False
						elif path[:1] == "_":
							to_remove.append(path)
					for d in to_remove:
						file_path.remove(d)

					if safe:
						if file_path:
							album_name = " - ".join(file_path)
						else:
							path = os.path.split(directory)
							if path[1]:
								album_name = path[1]
							else:
								album_name = os.path.split(path[0])[1]

						photos.append({"title": file, "path": os.path.join(root, file), "album": album_name})
		log.debug("All photos found.")
		return photos

	def GetPhotosToSync(self, albums, directory):
		log.debug("Running...")

		directory = os.path.realpath(directory)
		local = self.GetPhotosInDirectory(directory)
		(local_short, cloud, cloud_short, upload, delete) = ([], [], [], [], [])

		if albums:
			for album_name, album_id in albums.items():
				photos = self.GetPhotosInAlbum(album_id, album_name)
				if photos:
					cloud += photos[0]
					cloud_short += photos[1]
				else:
					return False
		else:
			return False

		for photo in local:
			short = [photo["album"], photo["title"]]
			if not short in cloud_short:
				upload.append(photo)
			else:
				local_short.append(short)
		log.info("%s photos found to upload.", str(len(upload)))

		for photo in cloud:
			if not [photo["album"], photo["title"]] in local_short:
				delete.append(photo)
		log.info("%s photos found to download / delete.", str(len(upload)))

		return (upload, delete)

	def SyncPhotos(self, directory, save, delete, upload, max, wait):
		log.info("Photo synchronization started.")
		albums = self.GetAlbums()
		(to_upload, to_delete) = self.GetPhotosToSync(albums, directory)
		(saved, notsaved, deleted, notdeleted, uploaded, notuploaded) = (0, 0, 0, 0, 0, 0)

		if save:
			log.info("Downloading photos from Flickr...")
			for photo in to_delete:
				dir = os.path.join(directory, photo["album"])
				if not os.path.exists(dir):
					try:
						os.makedirs(dir, 0o777)
					except:
						dir = directory
				if self.DownloadPhoto(photo, dir):
					saved += 1
				else:
					notsaved += 1

				if max and max <= saved:
					log.warning("Reached maximal number of downloads (%s)", str(max))
					break
				if wait:
					sleep(wait)
			log.info("%s photos downloaded, %s photos couldn't be downloaded", str(saved), str(notsaved))
		if delete and not save and (not max or saved < max):
			log.info("Deleting photos on Flickr...")
			for photo in to_delete:
				if self.DeletePhoto(photo["id"]):
					deleted += 1
				else:
					notdeleted += 1
			log.info("%s photos deleted, %s photos couldn't be deleted", str(deleted), str(notdeleted))
		if upload and (not max or saved < max):
			log.info("Uploading photos to Flickr...")
			for photo in to_upload:
				photo_id = self.UploadPhoto(photo["path"], {"title": photo["title"]})
				done = False
				if photo_id:
					if photo["album"] in albums:
						if self.AddPhotoToAlbum(photo_id, albums[photo["album"]]):
							done = True
					else:
						new_aldum_id = self.CreateAlbum(photo["album"], photo_id, False)
						albums[photo["album"]] = new_aldum_id
						if new_aldum_id:
							done = True
					if done:
						uploaded += 1
					else:
						self.DeletePhoto(photo_id)
						notuploaded += 1
				else:
					notuploaded += 1

				if max and max <= saved + uploaded:
					log.warning("Reached maximal number of downloads (%s)", str(max))
					break
				if wait:
					sleep(wait)

			log.info("%s photos uploaded, %s photos couldn't be uploaded", str(uploaded), str(notuploaded))

		return {
			"download": {
				"files": len(to_delete),
				"successful": saved,
				"failed": notsaved
			},
			"deletion": {
				"files": len(to_delete),
				"successful": deleted,
				"failed": notdeleted
			},
			"upload": {
				"files": len(to_upload),
				"successful": uploaded,
				"failed": notuploaded
			}
		}
