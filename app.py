import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
print(" [!] RUNNING APP.PY VERSION 2.0 (ASYNC FIX) [!]", flush=True)
import asyncio
import time
import httpx
import json
from collections import defaultdict
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from typing import Tuple
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
from google.protobuf import json_format, message
from google.protobuf.message import Message
from Crypto.Cipher import AES
import base64
import random

# === Settings ===
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB52"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
SUPPORTED_REGIONS = {"IND", "BR", "US", "SAC", "NA", "SG", "RU", "ID", "TW", "VN", "TH", "ME", "PK", "CIS", "BD", "EUROPE"}

# === Flask App Setup ===
app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens = defaultdict(dict)

# === Helper Functions ===
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def unpad(text: bytes) -> bytes:
    if not text:
        return text
    padding_length = text[-1]
    if padding_length > len(text):
         return text
    return text[:-padding_length]

def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    if not ciphertext or len(ciphertext) % 16 != 0:
        return ciphertext
    aes = AES.new(key, AES.MODE_CBC, iv)
    return unpad(aes.decrypt(ciphertext))

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    instance = message_type()
    instance.ParseFromString(encoded_data)
    return instance

async def json_to_proto(json_data: str, proto_message: Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def get_account_credentials(region: str) -> str:
    r = region.upper()
    if r == "IND":
        return "uid=3692279677&password=473AFFEF67F708CBB0962A958BB2809DA0843EA41BDB70D738FD9527EA04B27B"
    elif r in {"BR", "US", "SAC", "NA"}:
        return "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649"
    elif r == "VN":
        return "uid=3686689562&password=AD9C4A2B51A749481913F72A36F68A9F231520E9AC29B244DB47A64FD7353A12"
    elif r == "SG":
        return "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28"
    elif r == "ID":
        return "uid=3692307512&password=4AA06E1DB3F998ABDBDA74578D26B0C84700EC5C079751E7C8F1626048DDBCAE"
    elif r == "TH":
        return "uid=3692333198&password=0ED64C5A89E09B8BE538829B0304FE5F5F7EA3BBE645A341C73ECA49143D2211"
    elif r == "TW":
        return "uid=3692312456&password=1A062FD700DA8F826AF84A37EE2B62121B79516AF71666949C72FFF42D1C554A"
    else:
        try:
            with open("accounts.txt", "r") as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    raise ValueError("File accounts.txt trống.")
                uid, password = random.choice(lines).split()
                return f"uid={uid}&password={password}"
        except Exception as e:
            return f"ERROR: {e}"

# === Token Generation ===
async def get_access_token(account: str):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = account + "&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip", 'Content-Type': "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        data = resp.json()
        return data.get("access_token", "0"), data.get("open_id", "0")

async def create_jwt(region: str):
    account = get_account_credentials(region)
    token_val, open_id = await get_access_token(account)
    body = json.dumps({"open_id": open_id, "open_id_type": "4", "login_token": token_val, "orign_platform_type": "4"})
    proto_bytes = await json_to_proto(body, FreeFire_pb2.LoginReq())
    payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)
    url = "https://loginbp.ggblueshark.com/MajorLogin"
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
               'Content-Type': "application/octet-stream", 'Expect': "100-continue", 'X-Unity-Version': "2018.4.11f1",
               'X-GA': "v1 1", 'ReleaseVersion': RELEASEVERSION}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        msg = json.loads(json_format.MessageToJson(decode_protobuf(resp.content, FreeFire_pb2.LoginRes)))
        cached_tokens[region] = {
            'token': f"Bearer {msg.get('token','0')}",
            'region': msg.get('lockRegion','0'),
            'server_url': msg.get('serverUrl','0'),
            'expires_at': time.time() + 25200
        }

async def initialize_tokens():
    tasks = [create_jwt(r) for r in SUPPORTED_REGIONS]
    await asyncio.gather(*tasks)

async def refresh_tokens_periodically():
    while True:
        await asyncio.sleep(25200)
        await initialize_tokens()

async def get_token_info(region: str) -> Tuple[str,str,str]:
    info = cached_tokens.get(region)
    if info and time.time() < info['expires_at']:
        return info['token'], info['region'], info['server_url']
    await create_jwt(region)
    info = cached_tokens[region]
    return info['token'], info['region'], info['server_url']

async def GetAccountInformation(uid, unk, region, endpoint) -> dict:
    region = region.strip().strip('"').strip("'").upper()
    if region not in SUPPORTED_REGIONS:
        raise ValueError(f"Unsupported region: {region}")
    payload = await json_to_proto(json.dumps({'a': uid, 'b': unk}), main_pb2.GetPlayerPersonalShow())
    data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)
    token, lock, server = await get_token_info(region)
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
               'Content-Type': "application/octet-stream", 'Expect': "100-continue",
               'Authorization': token, 'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1",
               'ReleaseVersion': RELEASEVERSION}
    async with httpx.AsyncClient() as client:
        resp = await client.post(server+endpoint, data=data_enc, headers=headers)
        
        print(f" [!] GARENA RESPONSE: Status {resp.status_code}, Length {len(resp.content)} [!]", flush=True)
        log_path = os.path.abspath("debug.log")
        print(f" [!] Writing to log: {log_path} [!]", flush=True)
        with open(log_path, "a") as log:
             log_msg = f"[{time.ctime()}] Garena Status: {resp.status_code}, len: {len(resp.content)}, hex: {resp.content[:20].hex()}\n"
             log.write(log_msg)
             print(f"DEBUG LOG: {log_msg}", flush=True)
        
        content = resp.content
        try:
             # Try decoding directly
             return json.loads(json_format.MessageToJson(decode_protobuf(content, AccountPersonalShow_pb2.AccountPersonalShowInfo)))
        except:
             # Try decrypting first
             try:
                  decrypted = aes_cbc_decrypt(MAIN_KEY, MAIN_IV, content)
                  return json.loads(json_format.MessageToJson(decode_protobuf(decrypted, AccountPersonalShow_pb2.AccountPersonalShowInfo)))
             except Exception as e:
                  with open("debug.log", "a") as log:
                       log.write(f"[{time.ctime()}] Final Error: {str(e)}\n")
                  raise e



# === Caching Decorator ===
def cached_endpoint(ttl=300):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*a, **k):
            key = (request.path, tuple(request.args.items()))
            if key in cache:
                return cache[key]
            res = await fn(*a, **k)
            cache[key] = res
            return res
        return wrapper
    return decorator

# === Flask Routes ===

@app.route('/')
async def index():
    return jsonify({
        "name": "FreeFire Account Info API",
        "version": "1.0",
        "endpoints": {
            "/info": "Get account information (params: uid, region)",
            "/refresh": "Refresh tokens for all regions"
        },
        "supported_regions": list(SUPPORTED_REGIONS)
    })

@app.route('/info')
@cached_endpoint()
async def get_all_info():
    region = request.args.get('region', '').strip().strip('"').strip("'")
    uid = request.args.get('uid', '').strip().strip('"').strip("'")

    if not uid or not region:
        return jsonify({"error": "Please provide UID and REGION."}), 400

    try:
        # Avoid running nested asyncio loops, just await
        # In an 'async def' route, we just await
        return_data: dict = await GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow")
        
        # Ensure it's treated as a dict for the IDE
        if not isinstance(return_data, dict):
             return_data = {}
             
        result = {
            'basic_info': return_data.get('basicInfo', {}),
            'profile_info': return_data.get('profileInfo', {}),
            'ranking': return_data.get('rankingLeaderboardPos', {}),
            'news': return_data.get('news', {}),
            'history': return_data.get('historyEpInfo', {}),
            'clan_info': return_data.get('clanBasicInfo', {}),
            'captain_info': return_data.get('captainBasicInfo', {}),
            'pet_info': return_data.get('petInfo', {}),
            'social_info': return_data.get('socialInfo', {}),
            'diamond_costs': return_data.get('diamondCostRes', {}),
            'credit_score': return_data.get('creditScoreInfo', {}),
            'veteran_type': return_data.get('preVeteranType', 'N/A'),
            'equipped_achievements': return_data.get('equippedAch', {}),
            'uid': uid,
            'region': region
        }
        
        formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
        return formatted_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to get info: {str(e)}"}), 500

@app.route('/refresh', methods=['GET','POST'])
async def refresh_tokens_endpoint():
    try:
        await initialize_tokens()
        return jsonify({'message':'Tokens refreshed for all regions.'}),200
    except Exception as e:
        return jsonify({'error': f'Refresh failed: {e}'}),500
0

# === Startup ===
async def startup():
    await initialize_tokens()
    asyncio.create_task(refresh_tokens_periodically())

# Initialize tokens on first access
_tokens_initialized = False

@app.before_request
def initialize_if_needed():
    global _tokens_initialized
    if not _tokens_initialized:
        try:
            asyncio.run(initialize_tokens())
            _tokens_initialized = True
        except:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
