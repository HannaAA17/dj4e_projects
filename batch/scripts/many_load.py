import csv
from tqdm import tqdm

from unesco.models import Category, State, Region, Iso, Site

# https://django-extensions.readthedocs.io/en/latest/runscript.html
# python3 manage.py runscript many_load

def run():
    with open('unesco/whc-sites-2018-clean.csv') as f:
        reader = [*csv.DictReader(f)]

    Category.objects.all().delete()
    State.objects.all().delete()
    Region.objects.all().delete()
    Iso.objects.all().delete()
    Site.objects.all().delete()

    for row in tqdm(reader):
        # print(row)
        '''format:
        name,description,justification,year,longitude,latitude,area_hectares,
        category,state,region,iso
        '''
        category_, _ = Category.objects.get_or_create(name=row['category'])
        state_, _ = State.objects.get_or_create(name=row['state'])
        region_, _ = Region.objects.get_or_create(name=row['region'])
        iso_, _ = Iso.objects.get_or_create(name=row['iso'])

        # add null=True to numeric columns that can be empty in your models.py. 
        # check the data if not correct format assign it to None 
        # which will become NULL (or empty) in the data base when inserted:
        try:
            row['year'] = int(row['year'])
        except:
            row['year'] = None
        
        try:
            row['area_hectares'] = float(row['area_hectares'])
        except:
            row['area_hectares'] = None
        
        
        site_ = Site(
            name=row['name'],
            description=row['description'],
            justification=row['justification'],
            year=row['year'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            area_hectares=row['area_hectares'],
            category=category_,
            state=state_,
            region=region_,
            iso=iso_,
        )
        
        site_.save()