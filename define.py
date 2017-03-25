import requests
import json

def getDefinition(word):
    with open('words.txt', 'r') as handle:
        words = [line[:-1] for line in handle.readlines()]
        # print(words)

    # If this is not a word (perhaps a typo) do not attempt to define it.
    if word not in words:
        print("not showing up in words.txt")
        return None

    # Authentication information.
    headers = {
       "Accept": "application/json",
       "app_id": "d2cb3d21",
       "app_key": "a650f5f0a9a3da35157df5ab7d89d603"
    }
    r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/' +
                     'entries/en/' + word, headers=headers)

    # The word was not found.
    if r.status_code == 404:
        return None
    # Parse the data to obtain the word's definition and other useful info.
    data = json.loads(r.text)
    data = data["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]
    definition = data["definitions"][0]
    example = data["examples"][0]["text"]
    return (definition, example)
