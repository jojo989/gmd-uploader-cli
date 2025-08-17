import hashlib
import aiohttp
import urllib.parse
import zlib
import base64
from xml.dom import minidom
from typing import Dict, Union, Optional

# GMDData is represented as a dictionary with string keys and values that can be str, int, float, or None
GMDData = Dict[str, Union[str, int, float, None]]

async def account_id(username):
    data = urllib.parse.urlencode({
        'secret': 'Wmfd2893gb7',
        'str': username
    }).encode('utf-8')

    headers = {
        "User-Agent": "",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': str(len(data))
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://www.boomlings.com/database/getGJUsers20.php', data=data, headers=headers) as response:
            response_body = await response.text()

    user = response_body.split('|')[0].split(':')
    for i in range(0, len(user), 2):
        if int(user[i]) == 16:
            return int(user[i + 1])
    raise Exception("Account ID not found")

def generate_upload_seed(data, chars=50):
    if len(data) < chars:
        return data
    step = len(data) // chars
    result = ''
    for i in range(chars):
        result += data[i * step]
    return result

def xor_cipher(input_str, key):
    key_bytes = key.encode('utf-8')
    input_bytes = input_str.encode('utf-8')
    output_bytes = bytearray(len(input_bytes))

    for i in range(len(input_bytes)):
        output_bytes[i] = input_bytes[i] ^ key_bytes[i % len(key_bytes)]

    return output_bytes.hex()

def generate_chk(values=None, key="", salt=""):
    if values is None:
        values = []
    values.append(salt)
    string = ''.join(values)
    hash_obj = hashlib.sha1(string.encode('utf-8')).hexdigest()
    xored = xor_cipher(hash_obj, key)
    
    base64_url_safe = base64.b64encode(bytes.fromhex(xored)) \
        .decode('utf-8') \
        .replace('+', '-') \
        .replace('/', '_') \
        .rstrip('=')
    
    return base64_url_safe

def generate_seed(str_val):
    return generate_chk([generate_upload_seed(str_val)], "41274", "xI25fpAapCQg") + "=="

def generate_gjp2(password="", salt="mI29fmAnxgTs"):
    password += salt
    hash_obj = hashlib.sha1(password.encode('utf-8')).hexdigest()
    return hash_obj

def decode_level(data):
    base64_decoded = base64.b64decode(data.replace('_', '/').replace('-', '+'))
    decompressed = zlib.decompress(base64_decoded)
    return decompressed.decode('utf-8')

async def upload_level(username, password, levelname, leveldesc="", lvlstr="", audio_track=0, song_id=0, ver=21, unlisted=0):
    try:
        aid = await account_id(username)
        gjp = generate_gjp2(password)
        seed2 = generate_seed(lvlstr)
        
        data = urllib.parse.urlencode({
            'gameVersion': ver,
            'accountID': aid,
            'gjp2': gjp,
            'userName': username,
            'levelID': 0,
            'levelName': levelname,
            'levelDesc': base64.b64encode(leveldesc.encode('utf-8'))
                         .decode('utf-8')
                         .replace('+', '-')
                         .replace('/', '_')
                         .rstrip('='),
            'levelVersion': 127,
            'levelLength': 0,
            'audioTrack': audio_track,
            'auto': 0,
            'password': 0,
            'original': 0,
            'twoPlayer': 0,
            'songID': song_id,
            'objects': 1,
            'coins': 0,
            'requestedStars': 0,
            'unlisted': unlisted,
            'ldm': 0,
            'levelString': lvlstr,
            'seed2': seed2,
            'secret': 'Wmfd2893gb7',
        }).encode('utf-8')

        headers = {
            "User-Agent": "",
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data))
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.boomlings.com/database/uploadGJLevel21.php', data=data, headers=headers) as response:
                response_body = await response.text()

        return response_body
    except Exception as e:
        raise e

def parse_gmd_file(xml_content: str) -> GMDData:
    result: GMDData = {}
    xml_doc = minidom.parseString(xml_content)
    keys = xml_doc.getElementsByTagName('k')

    for key_elem in keys:
        key = key_elem.firstChild.nodeValue if key_elem.firstChild else None
        if key:
            value_elem = key_elem.nextSibling
            while value_elem and value_elem.nodeType != minidom.Element.ELEMENT_NODE:
                value_elem = value_elem.nextSibling
            if value_elem and value_elem.firstChild:
                value = value_elem.firstChild.nodeValue
                try:
                    if value.isdigit():
                        result[key] = int(value)
                    else:
                        result[key] = float(value)
                except ValueError:
                    result[key] = value
            else:
                result[key] = None

    return result

def get_gmd_value_by_key(xml_content: str, key_name: str) -> Optional[str]:
    xml_doc = minidom.parseString(xml_content)
    keys = xml_doc.getElementsByTagName('k')

    for key_elem in keys:
        current_key = key_elem.firstChild.nodeValue if key_elem.firstChild else None
        if current_key == key_name:
            value_elem = key_elem.nextSibling
            while value_elem and value_elem.nodeType != minidom.Element.ELEMENT_NODE:
                value_elem = value_elem.nextSibling
            return value_elem.firstChild.nodeValue if value_elem and value_elem.firstChild else None

    return None