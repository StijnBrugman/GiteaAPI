import requests
import json
from dataclasses import dataclass, asdict
from typing import List, Union
import datetime

from gtts import gTTS
from playsound import playsound
import threading


file_path_pr = 'merge.json'
file_path_m = 'pull_request.json'

api_url = "https://gitea.fledge.nl/api/v1"
repo_owner = "fledge_solutions"
repo_name = "bellbird"
token = "a72b48f92ea565e7097af65e14c9c3b320a45d5e"
WAIT_INTERVAL = 1

@dataclass
class prModel:
    id: int
    created_at: datetime.datetime
    name: str

@dataclass
class mergeModel:
    id: int
    merged_at: Union[datetime.datetime, None]
    name: str


pull_requests: List[prModel] = []
merge_requests: List[mergeModel] = []

def make_api_calls(api_url=api_url, repo_owner=repo_owner, repo_name=repo_name, token=token):
    merge_api_call()
    pull_api_call()
   
    # Wait for a specified interval and make the API calls again
    threading.Timer(WAIT_INTERVAL, make_api_calls, args=(api_url, repo_owner, repo_name, token)).start()


def pull_api_call(api_url=api_url, repo_owner=repo_owner, repo_name=repo_name, token=token):
    global pull_requests
    headers = {"Accept": "application/json"}
    pull_option_fields = f"state=open&sort=created&direction=desc&page=1&fields&token={token}"
    
    url = f"{api_url}/repos/{repo_owner}/{repo_name}/pulls?{pull_option_fields}"
    response = requests.get(url, headers=headers)

    print(f"[request] statusCode: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        new_pull_requests = list(map(lambda pr: prModel(pr['id'], pr['created_at'], pr['user']['full_name']), data))

        added_pull_requests = [item for item in new_pull_requests if item not in pull_requests]

        if (added_pull_requests): Text_to_speech("heeft een trek kwestie geopend", added_pull_requests[0].name)

        pull_requests = new_pull_requests
        data_list = [asdict(model) for model in new_pull_requests]
        write_data_to_file(file_path_pr, data_list)

    else:
        print(f"Error: {response.status_code} - {response.text}")

def merge_api_call(api_url=api_url, repo_owner=repo_owner, repo_name=repo_name, token=token):
    global merge_requests
    headers = {"Accept": "application/json"}
    merge_option_fields = 'state=closed&page=1'
    url = f"{api_url}/repos/{repo_owner}/{repo_name}/pulls?{merge_option_fields}&token={token}"
    response = requests.get(url, headers=headers)

    print(f"[request] statusCode: {response.status_code}")
    if response.status_code == 200:
        data = response.content
        data = json.loads(data)
        new_merge_requests = list(map(lambda pr: mergeModel(pr['id'], pr['merged_at'], pr['user']['full_name']), data))
        added_merge_requests = [item for item in new_merge_requests if item not in merge_requests] 
        
        if (added_merge_requests): Text_to_speech('heeft een trek kwestie gesloten', added_merge_requests[0].name)

        merge_requests = new_merge_requests

        data_list = [asdict(model) for model in new_merge_requests]
        write_data_to_file(file_path_m, data_list)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    

def write_data_to_file(file_path, data):
    with open(file_path, 'w') as file:
        file.truncate(0)
        json.dump(data, file, indent=4)


# check_and_update_dates(file_path, dates_array)
def init_api_requests():
    p_requests = []
    m_requests = []
    with open(file_path_pr, 'r') as file:
        try:
            p_requests = list(map(lambda pr: prModel(pr['id'], pr['created_at'], pr['name']), json.load(file)))
        except json.decoder.JSONDecodeError:
            pass
            
    with open(file_path_m, 'r') as file:
        try:
            m_requests = list(map(lambda pr: mergeModel(pr['id'], pr['merged_at'], pr['name']), json.load(file)))
        except json.decoder.JSONDecodeError:
            pass
    return p_requests, m_requests


# Kleine piemel
def Text_to_speech(message, name):
    speech = gTTS(text = name + message, lang = 'nl' )
    speech.save('DataFlair.mp3')
    playsound('DataFlair.mp3')


if __name__ == '__main__':
    pull_requests, merge_requests = init_api_requests()
    make_api_calls()
