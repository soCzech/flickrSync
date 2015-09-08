import hmac
import requests
from hashlib import sha1
from os.path import join
from binascii import b2a_base64
from time import localtime, strftime

from . import __logLevel__, __ver__, __key__, __secret__
from .helper import escape, generate_rand_num, generate_timestamp, \
	parameters_to_string, to_bytes, to_utf8, createJSON, orderJSON

class FlickrHandler():

	CONSUMER_KEY = __key__
	CONSUMER_SECRET = __secret__
	TOKEN = ""
	TOKEN_SECRET = ""

	def __init__(self, directory):
		self.DIR = directory
		self._restore()

	def build_signature(self, url, string_of_parameters, post):
		signature = [
			"POST" if post else "GET",
			escape(url),
			escape(string_of_parameters),
		]

		key = "%s&" % escape(self.CONSUMER_SECRET)
		if self.TOKEN_SECRET:
			key += escape(self.TOKEN_SECRET)
		raw = "&".join(signature)

		hashed = hmac.new(to_bytes(key), to_bytes(raw), sha1)
		return to_utf8(b2a_base64(hashed.digest())[:-1])

	def generate_params(self, url, data, post):
		if not hasattr(self, "oauth_nonce"): self.oauth_nonce = generate_rand_num(8)
		parameters = {
			"oauth_nonce": self.oauth_nonce,
			"oauth_timestamp": generate_timestamp(),
			"oauth_consumer_key": self.CONSUMER_KEY,
			"oauth_signature_method": "HMAC-SHA1",
			"oauth_version": "1.0"
		}

		parameters.update(data)
		string_of_parameters = parameters_to_string(orderJSON(parameters))
		signature = self.build_signature(url, string_of_parameters, post)

		if post:
			parameters.update({"oauth_signature": signature})
			return parameters
		else:
			return "%s?%s&oauth_signature=%s" % (url, string_of_parameters, signature)

	def handle_request(self, method, url, properties):
		boundary = str(generate_rand_num(20))
		requests.packages.urllib3.filepost.choose_boundary = lambda: boundary

		if method.upper() == "POST":
			if properties["files"]:
				headers = {"Content-type": "multipart/form-data; boundary=%s" % boundary}
			else:
				headers = {}

			r = requests.post(url, data=properties["data"], files=properties["files"], headers=headers)
		else:
			r = requests.get(url)

		if not r.text:
			r.text = {
				"stat": "fail",
				"message": "No text response received",
			}

		response = createJSON(r.text, r.status_code)
		self._log(response)
		return response

	def send_file(self, url, data, file):
		return self.handle_request("POST", url, {
			"data": self.generate_params(url, data, True),
			"files": {"photo": ("IMG.JPG", open(file, "rb"))}
		})

	def send_get(self, base_url, parameters):
		return self.handle_request("GET", self.generate_params(base_url, parameters, False), {})

	def send_post(self, url, data):
		return self.handle_request("POST", url, {
			"data": self.generate_params(url, data, True),
			"files": {}
		})

	def _debug(self, d, tabs):
		for k, v in orderJSON(d).items():
			if isinstance(v, dict):
				self.PRINT += tabs * "\t" + str(k) + ":\n"
				self._debug(v, tabs+1)
			elif isinstance(v, list):
				self.PRINT += tabs * "\t" + str(k) + ":\n"
				for i, t in enumerate(v):
					if isinstance(t, (dict, list)):
						self.PRINT += (tabs+1) * "\t" + "[" + str(i) + "]:\n"
						self._debug(t, tabs+2)
					else:
						self.PRINT += (tabs+1) * "\t" + "[" + str(i) + "]: " + t + "\n"
			else:
				self.PRINT += tabs * "\t" + str(k) + ": " + str(v) + "\n"

	def _log(self, d):
		if __logLevel__ == 10:
			self._debug(d, 0)
			f = open(join(self.DIR, "flickr.communication.dat"), "a+")
			f.write(self.PRINT + "\n")
			f.close()
			self._restore()

	def _restore(self):
		time = localtime()
		time = "%s@%s" % (strftime("%Y%m%d", time), strftime("%H%M%S", time))
		header = time + " ~ v" + __ver__
		self.PRINT = header + "\n" + len(header) * "-" + "\n"
