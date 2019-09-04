import requests
import time
import json

class ApiGitHub:
    def __init__(self,user, headers = { "Authorization": "token 4298820a4fa56a50b02c31343774abcc329e82f0" }):
        self.__user = user
        self.__headers = headers
        self.__queryCommitFull = """
            {
                user(login: "userName"){
                    name,
                    avatarUrl,
                    createdAt,    
                    pullRequests(pullRequestsConfig){
                        pageInfo{
                            endCursor,
                            hasNextPage,
                        }
                        totalCount,
                        nodes{
                            commits(last:100){
                                totalCount,
                                pageInfo{
                                    endCursor,
                                    hasNextPage 
                                }, 
                                nodes{
                                    resourcePath,
                                    pullRequest{
                                        number
                                    }
                                }
                            }
                        }
                    }
                },
                viewer {
                    login
                },
                rateLimit {
                    limit
                    cost
                    remaining
                    resetAt
                }
            }
            """
        self.queryCommitBig = """
            {
                user(login: "userName"){
                    name,
                    avatarUrl,
                    createdAt,    
                    pullRequests(first:1, states:MERGED){
                        pageInfo{
                            endCursor,
                            hasNextPage,
                        },
                        totalCount,
                        nodes{
                            repository{
                            pullRequest(number:NumberPull){
                                commits(first:100){
                                totalCount,
                                pageInfo{
                                    endCursor,
                                    hasNextPage 
                                }, 
                                nodes{
                                resourcePath
                                }
                                }
                            }
                        }
                            
                        }
                    }
            },
                viewer {
                    login
                }
                rateLimit {
                    limit
                    cost
                    remaining
                    resetAt
                }
            }

            """

    @staticmethod
    def performRequest(self, url, numTentativas = 10):
        tentativas = 0
        while(True):
            try:
                request = requests.get(url, headers=self.__headers)
                if(request.status_code == 200):
                    return request
                elif(tentativas > numTentativas):
                    return False
                else:
                    tentativas += 1
                    time.sleep(60)
            except requests.exceptions.RequestException as e: 
                print(e)
                time.sleep(10)
    
    def requestApiGitHubV4(self, query, numTentativas = 10):
        request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=self.__headers)
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    
    def getAlterateCommitPull(self, nodeCommit, perPage = 100):
        
        allPatchs = []
        totalCommit = nodeCommit['commits']['totalCount']
        numberPull = nodeCommit['commits']['nodes'][0]['resourcePath'].split('/')[4]

        if(totalCommit < perPage): #no caso de mais 100 commits em um pullrequest
            allPatchs = nodeCommit['commits']['nodes']
            # print(nodeCommit['commits']['totalCount'])
            # print('https://github.com' + nodeCommit['commits']['nodes'][0]['resourcePath'] + '.patch')
        else:
            for i in range(int(totalCommit/perPage)):
                result = self.requestApiGitHubV4(self.queryCommitBig.replace('userName', self.__user.loginUser).replace('NumberPull',numberPull))
                print(result)

        # for i,node in enumerate(nodeCommit['commits']['nodes']):
        #     # print('\tCommit',str(i + 1) + '/' + str(nodeCommit['commits']['totalCount']))
        #     url = 'https://github.com' + node['resourcePath'] + '.patch'
        #     req = self.performRequest(self,url) # obtem raw alteração
        #     if(not req):
        #         continue
            
    def getPullRequestUsers(self):
        pullRequestsConfig = 'first:100, states:MERGED'
        # cont = 0
        user = self.__user
        print(user.loginUser)
        while(True):
            result = self.requestApiGitHubV4(self.__queryCommitFull.replace('userName',user.loginUser).replace('pullRequestsConfig',pullRequestsConfig)) # Execute the query
            pullRequests = result["data"]["user"]['pullRequests']
            user.numberPullRequest = pullRequests['totalCount']
            for nodeCommit in pullRequests['nodes']:
                # cont += 1
                # print('pull nº ' , str(cont) + '/' + str(user.numberPullRequest))
                # self.getAlterateCommitPull( nodeCommit )
                self.getAlterateCommitPull( pullRequests['nodes'][18] )
                exit(0)
                         
            # print('remaining: ',result['data']['rateLimit'])
            # print('\n\n')
            endCursorPull = pullRequests['pageInfo']['endCursor']
            asNextPagePull = pullRequests['pageInfo']['hasNextPage']
            
            if(asNextPagePull):
                pullRequestsConfig = 'first:100, after:"{}", states:MERGED'.format(endCursorPull)
                #break #remover depois
            else:
                break
