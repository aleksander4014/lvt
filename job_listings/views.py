from django.shortcuts import render
from django.http import HttpResponse
import requests
import pandas
import json
from django.template.response import TemplateResponse

def currencyRate(currency):
    urlnbp = 'https://api.nbp.pl/api/exchangerates/rates/A/'+currency+'/?format=json'
    rnbp = requests.get(urlnbp)
    datanbp = json.loads(rnbp.text)
    rate = datanbp["rates"][0]["mid"]
    return rate

def get_job_listings(request):
    """
    View function to fetch and display remote job listings with salary information.
    """
    # Get plot area values from the form
    agricultural_area = request.GET.get('agricultural_area', 0)
    building_area = request.GET.get('building_area', 0)
    tag = request.GET.get('tag', '')
    region = request.GET.get('region',  '')

    
    # Convert to float, default to 0 if conversion fails
    try:
        agricultural_area = float(agricultural_area)
    except (ValueError, TypeError):
        agricultural_area = 0
        
    try:
        building_area = float(building_area)
    except (ValueError, TypeError):
        building_area = 0

    try:
        tag = str(tag).strip()
    except (ValueError, TypeError):
        tag = ''

    try:
        region = str(region)
    except (ValueError, TypeError):
        region = ''
    finally:
        Region = region.capitalize()

    url='https://jobicy.com/api/v2/remote-jobs?geo=' + str(region) + '&tag=' + str(tag)
    try:
        r = requests.get(url)
    except:
        return HttpResponse('Nie działa requests')

    try:    
        data = json.loads(r.text)
    except:
        return HttpResponse(url+' : '+r.text)
    
    try:
        df = pandas.DataFrame(data['jobs'])
    except KeyError:
        job_listings_html = '<p>Nie znaleziono ofert pracy</p>'
        return HttpResponse('Nie znaleziono ofert pracy '+ url)
    
    try:
        df2 = df[df['salaryMin'] > 0]
    except KeyError:
        return HttpResponse('Nie znaleziono ofert pracy z wynagrodzeniem')
    
    if df2.empty:
        return HttpResponse('Brak ofert pracy z wynagrodzeniem')
    
    # Select only the columns we want to display
    df2 = df2[['url', 'companyName', 'jobTitle', 'salaryMin', 'salaryCurrency', 'salaryPeriod']]
    df2['url']=df2['url'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
    df2=df2.reset_index(drop=True)
    # Normalize salary values to monthly
    for i, item in enumerate(df2['salaryPeriod']):
        if item == 'yearly':
            df2.loc[i, 'salaryMin'] = round(df2.loc[i, 'salaryMin'] / 12,2)
            #df2.loc[i, 'salaryMax'] = df2.loc[i, 'salaryMax'] / 12
            df2.loc[i, 'salaryPeriod'] = 'monthly'
        elif item == 'hourly':
            df2.loc[i, 'salaryMin'] = round(df2.loc[i, 'salaryMin'] * 40 * 4,2)  # 40 hours per week, 4 weeks per month,2)
            #df2.loc[i, 'salaryMax'] = df2.loc[i, 'salaryMax'] * 40 * 4
            df2.loc[i, 'salaryPeriod'] = 'monthly'
    
    ratesDict = {'USD': currencyRate('USD'),
                 'EUR': currencyRate('EUR'),
                 'GBP': currencyRate('GBP'),
                 'GHF': currencyRate('CHF'),
                 'CAD': currencyRate('CAD'),
                 'PLN': 1.0
                 }
    
    for i, item in enumerate(df2['salaryCurrency']):
        try:
            df2.loc[i, 'salaryMin'] = round(df2.loc[i, 'salaryMin'] * ratesDict[item],2)
            df2.loc[i, 'salaryCurrency'] = item+'/'+str(ratesDict[item])
        except KeyError:
            df2.loc[i, 'salaryMin'] = df2.loc[i, 'salaryMin']
            df2.loc[i, 'salaryCurrency'] = item+'/???'

    # Calculate LVT based on salary and plot areas
    # Base calculation
    base_lvt = df2['salaryMin'] 
    df2 = df2.rename(columns={'url': 'Url', 'companyName': 'Company', 'jobTitle': 'Job Title', 'salaryMin': 'Gross Salary (PLN)', 'salaryCurrency': 'Currency/Rate', 'salaryPeriod': 'Period'})
    # Adjust LVT based on plot areas if provided
    if agricultural_area > 0 or building_area > 0:
        # Example formula: Add 1% of LVT for each 100 m² of agricultural land and 5% for each 100 m² of building land
        agricultural_factor = agricultural_area * 0.25 / 12
        building_factor = building_area * 7.25 / 12
        
        # Apply the adjustment factors to the base LVT
        df2['Net salary after LVT'] = round(base_lvt - (agricultural_factor + building_factor),2)
    else:
        df2['Net salary after LVT'] = round(base_lvt,2)
    
    # Convert DataFrame to HTML
    job_listings_html = df2.to_html(index=False, border=1, escape=False)
    
    # Create a context dictionary to pass to the template
    context = {
        'job_listings_html': job_listings_html,
        'job_count': len(df2),
        'agricultural_area': agricultural_area,
        'building_area': building_area,
        'tag': tag,
        'region': region,
        'Region': Region
    }
    
    # Render the template with the context
    return render(request, 'job_listings/job_listings.html', context)

def home(request):
    """
    Home page view.
    """
    return render(request, 'job_listings/home.html')




