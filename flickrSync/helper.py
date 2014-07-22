import json
import xml.etree.ElementTree as ET

from time import time
from os.path import split
from random import randint
from urllib.request import quote
from collections import OrderedDict

def escape(s):
    return quote(s, safe="~")

def to_utf8(s):
	if isinstance(s, str):
		return s.encode("UTF-8")
	elif isinstance(s, bytes):
		return s.decode("UTF-8")
	else:
		return str(s)

def to_bytes(s):
	if isinstance(s, bytes):
		return s
	else:
		return str.encode(s)

def path_to_array(path):
    array = []
    while True:
        parts = split(path)
        if parts[0] == path:
            array.insert(0, parts[0])
            break
        else:
            path = parts[0]
            array.insert(0, parts[1])
    return array

def generate_rand_num(length = 8):
	return ''.join([str(randint(0, 9)) for i in range(length)])

def generate_timestamp():
	return str(time())

def parameters_to_string(p):
	try: del p["oauth_signature"]
	except: pass

	key_values = [(escape(to_utf8(k)), escape(to_utf8(v))) for k, v in p.items()]
	key_values.sort()
	return "&".join(["%s=%s" % (k, v) for k, v in key_values])
	
def createJSON(m, status):
	try:
		d = json.loads(m)
	except:
		try:
			s = ET.fromstring(m)
			d = s.attrib
			for c in s:
				if c.tag == "err":
					for k, v in c.attrib.items():
						d["message" if k == "msg" else k] = v
				else:
					d[c.tag] = {
						"text": c.text,
						"attrib": c.attrib
					}
		except:
			d = dict()
			n = (m + "&stat=" + ("ok" if status == 200 else "fail")).split("=")
			for i in range(len(n)-1):
				k = n[i][n[i].rfind("&")+1:]
				p = n[i+1].rfind("&")
				d[k] = n[i+1][:(len(n[i+1]) if p < 0 else p)]
	return d

def orderJSON(d):
	return OrderedDict(sorted(d.items()))