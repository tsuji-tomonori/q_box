import json

import requests

payload = {
    "type": "question",
    "question": {
        "name": "hoge",
        "date": "kyou",
        "question": "新しいやつ",
    }
}

url = "https://f97t9mlgql.execute-api.ap-northeast-1.amazonaws.com/prod/message"
topic = "sample"
r = requests.post(url=f"{url}/{topic}", data=json.dumps(payload))
