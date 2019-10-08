from src.controlDir import ControlDir
from src.query import Query
import requests
import math
import time
import json
from datetime import date


class ApiGitHub:
    def __init__(self, user, token):
        headers = {"Authorization": token}
        self.__user = user
        self.__headers = headers
        self.__urlApiV3 = 'https://api.github.com/search/repositories?q=language:{}&per_page={}&page=1&order=desc'

    def performRequest(self, url, numTentativas=10):
        tentativas = 0
        while (True):
            try:
                request = requests.get(url, headers=self.headers)
                if (request.status_code == 200):
                    return request
                elif (tentativas > numTentativas):
                    return False
                else:
                    tentativas += 1
                    time.sleep(60)
            except requests.exceptions.RequestException as e:

                print('performRequest: ', e)
                time.sleep(10)

    def requestApiGitHubV4(self, query, variables={}, numTentativa=20):
        while numTentativa > 0:
            try:
                request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=self.headers, timeout=30)
                if request.status_code == 200:
                    return request.json()
                else:
                    print('Tentativa Request Api V4 GitHub' + str(20 - numTentativa + 1))
                    if 'timeout' in request.json()["errors"][0]["message"]:
                        raise Exception
                    numTentativa -= 1
                    time.sleep(2)
            except:
                variables["numPage"] = (variables["numPage"] - 10) if variables["numPage"] > 10 else 10





    def getAlterateCommitPull(self, nodeCommit, perPage, state, dc, pwdCurrent):
        allPatchs = []
        totalCommit = nodeCommit['commits']['totalCount']
        numberPull = nodeCommit['commits']['nodes'][0]['resourcePath'].split('/')[4]

        if totalCommit < perPage:  # no caso de mais 100 commits em um pullrequest
            allPatchs = nodeCommit['commits']['nodes']
        else:
            commitInfo = 'first:{}'.format(perPage)
            for i in range(math.ceil(totalCommit / perPage)):  # arredonda flutuante pra cima (interio)
                try:
                    query = Query.getAllCommitForPullRequest(self.__user.loginUser, numberPull, commitInfo, state)
                    result = self.requestApiGitHubV4(query)

                    endCursor = \
                    result['data']['user']['pullRequests']['nodes'][0]['repository']['pullRequest']['commits'][
                        'pageInfo']['endCursor']
                    commitInfo = 'first:{}, after:"{}"'.format(perPage, endCursor)
                    allPatchs += \
                    result['data']['user']['pullRequests']['nodes'][0]['repository']['pullRequest']['commits']['nodes']
                except:
                    # api v4 nao econtra alguns pulls closed
                    pass

        for i, node in enumerate(allPatchs):
            print('\tCommit', str(i + 1) + '/' + str(totalCommit))
            url = 'https://github.com' + node['resourcePath'] + '.patch'

            pwd = pwdCurrent + '\\' + url.split('/')[6]
            if i == 0:
                dc.newDirectory(pwd)

            req = self.performRequest(url)  # obtem raw alteração

            if req:
                file = open(pwd + '\\' + node['commit']['abbreviatedOid'] + '.txt', 'w', encoding="utf-8")
                file.write(req.text)
                file.close()

    def getPullRequestUsers(self, perPage=100):

        states = ['MERGED', 'OPEN', 'CLOSED']
        user = self.user
        dc = ControlDir(user.loginUser)  # cria arquivo user

        for state in states:
            pullRequestsConfig = 'first:{}, states:{}'.format(perPage, state)
            cont = 0
            pwdCurrent = dc.userDirectory + '\\' + state
            dc.newDirectory(pwdCurrent)  # adiciona Status ao diretorio
            print(user.loginUser)
            print(state)

            while True:
                query = Query.getMax100CommitForPullRequests(user.loginUser, pullRequestsConfig)

                result = self.requestApiGitHubV4(query)  # Execute the query

                pullRequests = result["data"]["user"]['pullRequests']
                user.numberPullRequest = pullRequests['totalCount']
                for nodeCommit in pullRequests['nodes']:
                    cont += 1
                    print('pull nº ', str(cont) + '/' + str(user.numberPullRequest))
                    self.getAlterateCommitPull(nodeCommit, perPage, state, dc, pwdCurrent)

                endCursorPull = pullRequests['pageInfo']['endCursor']
                asNextPagePull = pullRequests['pageInfo']['hasNextPage']

                if asNextPagePull:
                    pullRequestsConfig = 'first:{}, after:"{}", states:{}'.format(perPage, endCursorPull, state)
                else:
                    break

    def getUserFromRep(self, linguages, numeroContribuidores=10, numeroProjetos=5):
        listRepo = {}
        for language in linguages:
            print(language)
            url = self.urlApiV3.format(language.lower(), numeroProjetos)
            # print(url)
            request = self.performRequest(url)
            print(request)
            listRepo[language] = []
            for proj in request.json()['items']:
                url = proj['contributors_url'] + '?per_page=' + str(numeroContribuidores)
                print(url)
                requestUser = self.performRequest(url).json()
                contributors = [urlUser['login'] for urlUser in requestUser]
                listRepo[language].append({proj['full_name']: contributors})
        file = open('ProjWithUser.json', 'w')
        json.dump(listRepo, file, indent=4)
        file.close()

    def getUserInf(self):
        query = Query.userPerfilInfo(self.user.loginUser)
        return self.requestApiGitHubV4(query)

    def getUserInfByYear(self):
        dateCreated = self.user.createdAt.split("-")
        yearCreated = int(dateCreated[0])
        monthCreated = int(dateCreated[1])
        flagMonth = True

        todayDate = str(date.today()).split('-')
        todayYear = int(todayDate[0])
        todayMonth = int(todayDate[1])
        userYearInfo = {}

        while yearCreated <= todayYear:
            yearCreated = yearCreated

            if flagMonth:
                month = monthCreated
                flagMonth = False
            else:
                month = 1

            userMonthinfo = {}
            print(yearCreated)
            while True:
                if month > 12 or (yearCreated == todayYear and month > todayMonth):
                    break

                monthAux = str(month)
                monthAux = (str(0) + monthAux) if month < 10 else monthAux
                print(monthAux)
                query = Query.userInfoContributionsCollection(self.user.loginUser, str(yearCreated), monthAux)
                userMonthinfo[month] = self.requestApiGitHubV4(query)["data"]["user"]["contributionsCollection"]
                month += 1

            userYearInfo[yearCreated] = userMonthinfo
            yearCreated += 1

        return userYearInfo

    def getUserCommitContribution(self):
        query = Query.userCommitContribution()
        return self.requestApiGitHubV4(query)

    def pullRequestContribution(self, nameUser, numPage=100):# maior q isso timeout
        queryVariables = {
            "nameUser": nameUser,
            "numPage": numPage
        }
        RepositoryAffiliation = {'OWNER': [], 'COLLABORATOR': [], 'ORGANIZATION_MEMBER': []}
        for repAff in RepositoryAffiliation.keys():
            queryVariables["RepositoryAffiliation"] = repAff
            after = ''

            while True:
                query = Query.repInfo(after)
                resp = self.requestApiGitHubV4(query, queryVariables)
                RepositoryAffiliation[repAff] += resp['data']['user']['repositories']['nodes']
                if not resp['data']['user']['repositories']['pageInfo']['hasNextPage']:
                    break
                after = resp['data']['user']['repositories']['pageInfo']['endCursor']

        return RepositoryAffiliation['OWNER'], RepositoryAffiliation['COLLABORATOR'], RepositoryAffiliation['ORGANIZATION_MEMBER']


    @property
    def user(self):
        return self.__user

    @property
    def headers(self):
        return self.__headers

    @property
    def urlApiV3(self):
        return self.__urlApiV3
