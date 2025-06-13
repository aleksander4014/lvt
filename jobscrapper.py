import requests
import pandas
import json

def hello_world():
    r=requests.get('https://jobicy.com/api/v2/remote-jobs')
    data = json.loads(r.text)
    try:
        df = pandas.DataFrame(data['jobs'])
    except KeyError:
        df3='Nie udało się znaleźć ofert pracy'
    else:
        try:
            df2=df[df['salaryMin']>0]
        except KeyError:
            df3='Nie znaleziono ofert pracy z wynagrodzeniem'
        else:
            df2=df2[['url', 'companyName', 'jobTitle', 'salaryMin', 'salaryMax', 'salaryCurrency', 'salaryPeriod']]
            df2=df2.reset_index(drop=True)
            print('piwo'.capitalize())

    try:
        df3=df2.to_html(buf=None,index=False, border=1, escape=False)
    except:
        df3='Brak ofert pracy z wynagrodzeniem'

    return 0

print(hello_world())