import os
import re
import sys
import webbrowser

from time import sleep
from inspect import stack
from urllib.request import urlopen, unquote

from .helper import path_to_array
from .flickrhandler import FlickrHandler
from . import __app__, __dev__, __callback__, __exclude__

data_file = "flickr.session.dat"

base = "https://api.flickr.com/services"
rest = base + "/rest"
upload = base + "/upload"
auth_rt = base + "/oauth/request_token"
auth_at = base + "/oauth/access_token"

msg = {
	"auth": "\tOAuth needed",
	"deletion": "\tDeleting...",
	"download": "\tDownloading...",
	"error_": "\tError while ",
	"exc_": "\tEXCEPTION: ",
	"fail": "\tFunction failed",
	"failed": " failed",
	"success": "\tSuccess",
	"upload": "\tUploading..."
}

def dev(m):
	if __dev__:
		print(m)

class FlickrAPI():
	def __init__(self, directory):
		print(__app__ + "\n" + len(__app__) * "-")
		self.DIR = directory
		self.API = FlickrHandler(self.DIR)
	
	"""
		OAuth
	"""

	def CheckTokens(self):
		print(stack()[0][3])

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
			print(msg["error_"] + "accessing session file")
			dev(msg["exc_"] + e)
		finally:
			if not self.API.TOKEN:
				print(msg["auth"])
				return False
			else:
				print(msg["success"])
				return True

	def OAuthSingIn(self):
		print(stack()[0][3])

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

			print("\tAuthorize in browser using this URL\n\t" + url)
			print("\tEnter your oauth_verifier from callback URL")

			verifier = input("\t\t")
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

					print("\tSigned in as " + unquote(resp_verifier["fullname"]))
					return True

		print(msg["fail"])
		return False
	
	"""
		Individual photo functions
	"""

	def AddPhotoToAlbum(self, photo_id, album_id):
		_fn_ = stack()[0][3] + " % " + str(photo_id) + ", " + str(album_id)
		dev(_fn_)

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
			dev(msg["success"])
			return True

		print("\t" + _fn_ + msg["failed"])
		return False

	def DeletePhoto(self, photo_id):
		_fn_ = stack()[0][3] + " % " + str(photo_id)
		dev(_fn_)

		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photos.delete",
			"photo_id": photo_id,
			"format": "json",
			"nojsoncallback": 1
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			dev(msg["success"])
			return True

		print("\t" + _fn_ + msg["failed"])
		return False

	def DownloadPhoto(self, photo, directory):
		_fn_ = stack()[0][3] + " % " + photo["title"] + ", " + directory
		dev(_fn_)

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
			dev(msg["success"])
			return True
		except:
			pass
		print("\t" + _fn_ + msg["failed"])
		return False
		
	def UploadPhoto(self, file, data):
		_fn_ = stack()[0][3] + " % " + file + ", " + ", ".join(data.values())
		dev(_fn_)

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
			dev(msg["success"])
			return resp["photoid"]["text"]

		print("\t" + _fn_ + msg["failed"])
		return False
	
	"""
		Album functions
	"""

	def CreateAlbum(self, name, primary_photo_id, description):
		_fn_ = stack()[0][3] + " % " + name
		dev(_fn_)

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
			dev(msg["success"])
			return resp["photoset"]["id"]

		print("\t" + _fn_ + msg["failed"])
		return False

	def GetAlbumIdByName(self, name):
		_fn_ = stack()[0][3] + " % " + name
		dev(_fn_)

		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.getList",
			"format": "json",
			"nojsoncallback": 1
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			for album in resp["photosets"]["photoset"]:
				if album["title"]["_content"] == name:
					dev(msg["success"])
					return album["id"]
			dev(msg["success"])
			return None
		print("\t" + _fn_ + msg["failed"])
		return False

	def GetAlbums(self):
		dev(stack()[0][3])

		parameters = {
			"oauth_token": self.API.TOKEN,
			"method": "flickr.photosets.getList",
			"format": "json",
			"nojsoncallback": 1
		}

		resp = self.API.send_post(rest, parameters)

		if resp["stat"] == "ok":
			albums = []
			for album in resp["photosets"]["photoset"]:
				albums.append({"id": album["id"], "name": album["title"]["_content"]})
			dev(msg["success"])
			return albums

		print("\t" + stack()[0][3] + msg["failed"])
		return False

	def GetPhotosInAlbum(self, album_id, album_name):
		_fn_ = stack()[0][3] + " % " + str(album_id) + ", " + album_name
		dev(_fn_)

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
				print("\t" + _fn_ + msg["failed"])
				return False
			parameters["page"] += 1

		dev(msg["success"])
		return (photos, photos_short)

	"""
		Synchronization functions
	"""

	def GetPhotosInDirectory(self, directory):
		dev(stack()[0][3] + " % " + directory)

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
		dev(msg["success"])
		return photos

	def GetPhotosToSync(self, directory):
		dev(stack()[0][3] + " % " + directory)

		directory = os.path.realpath(directory)
		local = self.GetPhotosInDirectory(directory)
		(local_short, cloud, cloud_short, upload, delete) = ([], [], [], [], [])

		albums = self.GetAlbums()
		if albums:
			for album in albums:
				photos = self.GetPhotosInAlbum(album["id"], album["name"])
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
		print("\t" + str(len(upload)) + " photos to upload found")

		for photo in cloud:
			if not [photo["album"], photo["title"]] in local_short:
				delete.append(photo)
		print("\t" + str(len(delete)) + " photos to download / delete found")

		return (upload, delete)

	def SyncPhotos(self, directory, save, delete, upload, max, wait):
		print(stack()[0][3] + " % " + directory)
		(to_upload, to_delete) = self.GetPhotosToSync(directory)
		(saved, notsaved, deleted, notdeleted, uploaded, notuploaded) = (0, 0, 0, 0, 0, 0)
		albums = {}

		if save:
			if not __dev__:
				print(msg["download"])
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
					print("\tReached maximal number of downloads (" + str(max) + ")")
					break
				if wait:
					sleep(wait)
			print("\tDownload " + str(saved) + " times successful, " + str(notsaved) + " times failed")
		if delete and notsaved == 0 and (not max or saved < max):
			if not __dev__:
				print(msg["deletion"])
			for photo in to_delete:
				if self.DeletePhoto(photo["id"]):
					deleted += 1
				else:
					notdeleted += 1
			print("\tDeletion " + str(deleted) + " times successful, " + str(notdeleted) + " times failed")
		elif delete and not notsaved == 0:
			print("\tDeletion not initiated, not all photos successfully saved")
		if upload and (not max or saved < max):
			if not __dev__:
				print(msg["upload"])
			for photo in to_upload:
				photo_id = self.UploadPhoto(photo["path"], {"title": photo["title"]})
				done = False
				if photo_id:
					if photo["album"] in albums:
						album_id = albums[photo["album"]]
					else:
						album_id = self.GetAlbumIdByName(photo["album"])
					if album_id:
						if not photo["album"] in albums:
							albums.update({photo["album"]: album_id})
						if self.AddPhotoToAlbum(photo_id, album_id):
							done = True
					elif album_id == None:
						if self.CreateAlbum(photo["album"], photo_id, False):
							done = True
					if done:
						uploaded += 1
					else:
						self.DeletePhoto(photo_id)
						notuploaded += 1
				else:
					notuploaded += 1
				
				if max and max <= saved + uploaded:
					print("\tReached maximal number of downloads / uploads (" + str(max) + ")")
					break
				if wait:
					sleep(wait)

			print("\tUpload " + str(uploaded) + " times successful, " + str(notuploaded) + " times failed")

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