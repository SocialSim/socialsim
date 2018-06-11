import json

communities = ['cpp', 'java', 'linux']

with open('an_RepoTopics_fixed.json', 'r') as file:
    data = json.load(file)

community_has_repos = dict()

for c in communities:
    for i in data:
        if i['topic'] == c:
            community_has_repos[c] = i['repos_h']

with open('community_has_repos.json', 'w') as file:
    json.dump(community_has_repos, file, indent=4)
