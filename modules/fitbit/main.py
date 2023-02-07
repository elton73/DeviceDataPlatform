import authentication as auth
import time, retrieve


if __name__=="__main__":
    auth_token = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyM0JIWTciLCJzdWIiOiJCNVhMNTciLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyYWN0IHJzZXQgcndlaSByaHIgcm51dCByc2xlIiwiZXhwIjoxNjYyNTI0ODE4LCJpYXQiOjE2NjI0OTYwMTh9.rDsgrsrNQs24uT4ZLjz-aqZ4tq3Q8zwwhWIisByKftE'
    refresh_token = '915724a9d19a33b8641df881aaaa88c73b200d5cb8e8c62e6801636eda837dfa'

    sleepPeriod = 3600      # 1 hour in seconds
    tokenPeriod = 14400     # 4 hours in seconds
    lastTime = time.time()

    while True:
        curTime = time.time()
        if (curTime - lastTime) > tokenPeriod:
            refresh_token = auth.get_refreshed_fitbit_auth_info(refresh_token)
            print(refresh_token, curTime)
            lastTime = curTime

        DataGet = retrieve.DataGetter(auth_token)
        print(DataGet.get_all_devices().json())
        
        print("="*50)
        # print(DataGet.get_intraday_heart(startDate='today', endDate='today').json())

        time.sleep(sleepPeriod)

    # cnx.close()