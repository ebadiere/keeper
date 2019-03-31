#!/usr/bin/env python
import requests

url = "https://sai-mainnet.makerfoundation.com/v1"

payload = "query=%7B%0A%20%20allCups(%0A%20%20%20%20first%3A%2010%2C%0A%20%20%20%20condition%3A%20%7B%20deleted%3A%20false%20%7D%2C%0A%20%20%20%20orderBy%3A%20RATIO_ASC%0A%20%20)%20%7B%0A%20%20%20%20totalCount%0A%20%20%20%20pageInfo%20%7B%0A%20%20%20%20%20%20hasNextPage%0A%20%20%20%20%20%20hasPreviousPage%0A%20%20%20%20%20%20endCursor%0A%20%20%20%20%7D%0A%20%20%20%20nodes%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20lad%0A%20%20%20%20%20%20art%0A%20%20%20%20%20%20ink%0A%20%20%20%20%20%20ratio%0A%20%20%20%20%20%20actions(first%3A%205)%20%7B%0A%20%20%20%20%20%20%20%20nodes%20%7B%0A%20%20%20%20%20%20%20%20%20%20act%0A%20%20%20%20%20%20%20%20%20%20time%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D&undefined="
headers = {
    'Content-Type': "application/x-www-form-urlencoded",
    'cache-control': "no-cache",
    'Postman-Token': "8e94b354-f486-4900-94ff-5aaf6b533f87"
    }

response = requests.request("POST", url, data=payload, headers=headers)

print(response.text)