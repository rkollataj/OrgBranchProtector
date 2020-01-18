#!/bin/python3
from ghapi_v3 import GhComm, GhBranchProtection
from flask import Flask, request, redirect
from time import sleep
import json
import requests

app = Flask(__name__)

@app.route("/", methods=['GET'])
def hello():
    return redirect("https://github.com/rkollataj/OrgBranchProtector", code=302)

@app.route("/webhook", methods=['GET'])
def webhook():
    code = request.args.get('code')
    
    payload = { 
        "client_id" : "2bd1e2acc55a937922c8",
        "client_secret" : "c9e95cb63dec811cf40503c0f3d9e9512316d94b",
        "code" : code
    }

    print(payload)

    headers = { 
        "Content-Type": "application/json",
        "Accept": "application/json" 
    }

    rsp = requests.post("https://github.com/login/oauth/access_token", data=json.dumps(payload), headers=headers)

    if 200 <= rsp.status_code < 300:
        t = json.loads(rsp.text)["access_token"]

        rsp2 = requests.get("https://api.github.com/user", headers={ "Authorization" : "token {}".format(t) } )

        if 200 <= rsp2.status_code < 300:
            login = json.loads(rsp2.text)["login"]

            return """Webhook address to use for your organization:<br>
                      <b>https://ghbranchprotector.azurewebsites.net/repository/{}/{}</b>
                      <br><br>
                      <b>NOTE:</b> Passing access_token in path is potential security breach. Be sure that you are testing<br>
                      the app on dummy organization. You can always revoke application access by visiting<br>
                      'third-party access' section in your organization settings""".format(login, t)

    return "Failed to authorize the app"

@app.route("/authorize", methods=['GET'])
def authorize():
    return redirect("https://github.com/login/oauth/authorize?client_id=2bd1e2acc55a937922c8&scope=repo", code=302)

@app.route("/repository/<user>/<token>", methods=['POST'])
def projects(user, token):
    p = request.json

    if p["action"] == "created" :
        repoName = p["repository"]["name"]
        org = p["organization"]["login"]
        branch = p["repository"]["default_branch"]

        bps = GhBranchProtection()
        bps.setRestrictionsUsers(user)
        bps.setReview(2, users=user)
        bps.setStatusChecks(True, ["build_result", "static_code_check"])

        repo = GhComm(org, repoName, token)

        branchExists = repo.checkBranchExists(branch);
        checkCnt = 0;
        while (not branchExists) and (checkCnt < 3):
            # When user choses initialization with README
            # It will take GitHub some time to process
            branchExists = repo.checkBranchExists(branch);
            checkCnt += 1
            sleep(0.25)

        if not branchExists:
            repo.initWithReadme()

        repo.updateBrachProtection(bps)
        repo.createIssue("You shall not push!", bps.toHuman(branch, user))

        return "Branch protections settings applied for {}/{} '{}' branch".format(org, repoName, branch)
    
    return "No processing"
