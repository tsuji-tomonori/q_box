import datetime
import json

import requests

payload = {
    "type": "question",
    "question": {
        "name": "hoge",
        "date": f"{datetime.datetime.utcnow().isoformat()[:-3]}Z",
        "question": "新しいやつ",
    }
}

url = "https://f97t9mlgql.execute-api.ap-northeast-1.amazonaws.com/prod/message"
topic = "sample"
r = requests.post(url=f"{url}/{topic}", data=json.dumps(payload))
