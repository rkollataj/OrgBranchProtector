#!/bin/python3

import json
import requests
import hashlib
import base64

class GhBranchProtection:
    data = {
        "required_status_checks": None,
        "enforce_admins": None,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_linear_history" : False,
    }

    def _validateListStr(self, l):
        if type(l) is not list :
            raise ValueError("Expected paramter type: str or list[str]")

        if type(l) is list :
            for u in l:
                if type(u) is not str :
                    raise ValueError("Expected paramter type: str or list[str]")

    def setRestrictionsUsers(self, users) :
        if self.data["restrictions"] is None :
            self.data["restrictions"] = { "users": [],  "teams": [], "apps": [] }

        # if user pass signle user
        if type(users) is str :
            users = [ users ]
        self._validateListStr(users)

        self.data["restrictions"]["users"] = users

    # set count <= 0 to disable
    def setReview(self, count, users=[], teams=[], dismiss_stale_reviews=True, require_code_owner_reviews=True):
        if count <= 0:
            self.data["required_pull_request_reviews"] = None
        else:
            # if user pass signle user
            if type(users) is str :
                users = [ users ]
            self._validateListStr(users)

            # if user pass signle user
            if type(teams) is str :
                teams = [ teams ]
            self._validateListStr(teams)

            self.data["required_pull_request_reviews"] = {
                  "dismissal_restrictions" : { "users" : users, "teams" : teams }, 
                  "dismiss_stale_reviews" : dismiss_stale_reviews,
                  "require_code_owner_reviews" : require_code_owner_reviews,
                  "required_approving_review_count" : count
                }
    def setStatusChecks(self, strict, contexts):
        self.data["required_status_checks"] = { "strict" : strict, "contexts" : contexts }

    def toHuman(self, branch, user) :
        desc = "You're beloved administrator (@{}) configured protection for '{}' branch. You are not allowed to push your code to it directly and need to issue Pull Request instead.\n\n".format(user, branch)
        
        if self.data["restrictions"] != None:
            users = self.data["restrictions"]["users"]
            teams = self.data["restrictions"]["teams"]
            apps = self.data["restrictions"]["apps"]

            if len(users) > 0 or len(teams) > 0 or len(apps) > 0:
                desc += "Push permisions are limited to:\n"

                if len(users) > 0 :
                    desc += "* users: **__{}__**\n".format(str(users))

                if len(teams) > 0 :
                    desc += "* teams: **__{}__**\n".format(str(teams))

                if len(apps) > 0 :
                    desc += "* apps: **__{}__**\n".format(str(apps))
                
                desc += "\n"

        if self.data["required_pull_request_reviews"] != None:
            desc += "Pull Request review settings:\n"
            if self.data["required_pull_request_reviews"]["dismissal_restrictions"] != None:
                users = self.data["required_pull_request_reviews"]["dismissal_restrictions"]["users"]
                teams = self.data["required_pull_request_reviews"]["dismissal_restrictions"]["teams"]

                desc += "* Review dismissal is restricted to:\n"

                if len(users) > 0 :
                    desc += "    * users: **__{}__**\n".format(str(users))

                if len(teams) > 0 :
                    desc += "    * teams: **__{}__**\n".format(str(teams))
                
            desc += "* Automatic dismissal of approving reviews is **__{}__**\n".format("enabled" if self.data["required_pull_request_reviews"]["dismiss_stale_reviews"] else "disabled")
            desc += "* [Code owners](https://help.github.com/articles/about-code-owners/) review is **__{}__**\n".format("required" if self.data["required_pull_request_reviews"]["require_code_owner_reviews"] else "not required")
            desc += "* Number of required approvers: **__{}__**\n".format(self.data["required_pull_request_reviews"]["required_approving_review_count"])
            # desc += "* **__{}__**\n".format("enabled" if self.data["required_pull_request_reviews"][""] else "disabled")

        if self.data["required_status_checks"] != None:
            desc += "\nStatus checks configuration:\n"
            desc += "* Branches **__{}__** to be up to date before merging\n".format("need" if self.data["required_status_checks"]["strict"] else "don't have")
            desc += "* Required status checks before merging: **__{}__**\n".format(str(self.data["required_status_checks"]["contexts"]))

        desc += "\nAdditional settings:\n"
        desc += "* Linear history is **__{}required__**\n".format(" " if self.data["required_linear_history"] else "not ")
        desc += "* Force pushes for users with write permissions are **__{}allowed__**\n".format("" if self.data["allow_force_pushes"] else "not ")
        desc += "* Deletion of this branch for users with write permissions is **__{}allowed__**\n".format("" if self.data["allow_deletions"] else "not ")
        desc += "* All of the above restrictions **__{}__** to administrators\n".format("applies" if self.data["enforce_admins"] else "does not apply") 

        return desc

    def toJson(self) :
        return json.dumps(self.data)

class GhComm:
    def __init__(self, org, repo, token):
        self.repo = "https://api.github.com/repos/" + org + "/" + repo
        self.token = token
        self.repoName = repo

    def updateBrachProtection(self, bps):
        headers = {
            "Authorization" : "token {}".format(self.token),
            "Accept":"application/vnd.github.luke-cage-preview+json"
        }

        rsp = requests.put(self.repo + "/branches/master/protection", data=bps.toJson(), headers=headers)
        if 200 <= rsp.status_code < 300:
            print("Brach protection updated")
        else:
            print(rsp)
            print(rsp.text)
            raise RuntimeError("Unsuccesufl change of branch protection settings")

    def createIssue(self, title, body):
        headers = {
            "Authorization" : "token {}".format(self.token)
        }

        payload = { "title": title, "body": body }
        rsp = requests.post(self.repo + "/issues", data=json.dumps(payload), headers=headers)

        if 200 <= rsp.status_code < 300:
            print("Issue created")
        else:
            print(rsp)
            print(rsp.text)
            raise RuntimeError("Failed to create issue")

    def checkBranchExists(self, name):
        headers = {
            "Authorization" : "token {}".format(self.token)
        }

        rsp = requests.get(self.repo + "/branches", headers=headers)

        if not 200 <= rsp.status_code < 300:
            print(rsp)
            print(rsp.text)
            raise RuntimeError("Failed to create issue")

        branches = json.loads(rsp.text)
        for b in branches:
            if name == b["name"]:
                return True

        return False

    def createBranch(self, name):
        headers = {
            "Authorization" : "token {}".format(self.token)
        }

        payload = { "ref" : "refs/heads/"+name, "sha" : hashlib.sha1().hexdigest() }
        rsp = requests.post(self.repo + "/git/refs", data=json.dumps(payload), headers=headers)

        print(rsp)
        print(rsp.text)

    def initWithReadme(self):
        headers = {
            "Authorization" : "token {}".format(self.token)
        }

        content = base64.b64encode(bytes("# " + self.repoName, 'utf-8'))
        payload = { 
            "message" : "Initial version", 
            "committer" : {
                "name" : "Mr. Robot",
                "email" : "mr@robot.com"
                },
            "content" : content.decode("utf-8")
            }
        rsp = requests.put(self.repo + "/contents/README.md", data=json.dumps(payload), headers=headers)

        if 200 <= rsp.status_code < 300:
            print("Repository initialized")
        else:
            print(rsp)
            print(rsp.text)
            raise RuntimeError("Failed to initialize repository")

