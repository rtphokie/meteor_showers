import unittest
import requests_cache
import bs4
from pprint import pprint
import re
from datetime import datetime


class ams():
    url = 'https://www.amsmeteors.org/meteor-showers/meteor-shower-calendar/'

    def __init__(self):
        self.session = requests_cache.CachedSession('.ams_cache.sqlplus')

    def parse(self):
        showers = []
        rex = re.compile(r'[\W,]+')
        r = self.session.get(ams.url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        divs = soup.find_all('div', {'class': 'media-body'})
        for div in divs:
            h3 = div.find('h3', {'class': 'media-heading'})
            active = div.find('span', {'class': 'shower_acti'})
            paragraphs = div.find_all('p')
            desc = paragraphs[0]

            name = re.sub("\s+", " ", h3.text).strip()
            active_str = re.sub("\s+", " ", active.text).strip()
            active_str = re.sub(r'(\d+)[stndrh]+', r'\1', active_str)  # remove ordinal
            active_to = None
            active_from = None
            if match := re.search('Active from ([\w\s,]+) to ([\w\s,]+)', active_str, re.IGNORECASE):
                active_from_str = match.group(1)
                active_from_date = self.extract_date(active_from_str)
                active_to_str = match.group(2)
                active_to_date = self.extract_date(active_to_str)
                if active_from_date.year == 1900:
                    active_from_date = active_from_date.replace(year=active_to_date.year)

            data = {'name': name, 'active_str': active_str, 'active_to': active_to_date,
                    'active_from': active_from_date, 'description': desc.text,
                    }
            details = re.sub("\s+", " ", paragraphs[1].prettify().replace('<p>', '').replace('</p>', '')).strip()
            details = details.replace('<p>', '')
            for thing in details.split('<strong>'):
                if 'strong' in thing:
                    strongstr, value = thing.split('</strong>')
                    value = value.rstrip(' -').strip()
                    strong = bs4.BeautifulSoup(f"<strong>{strongstr}", features="html.parser")
                    param = strong.text
                    param = param.strip().rstrip(':').strip()
                    if value and len(value) > 0:
                        data[param] = value
                        if param == 'ZHR' :
                            data[param] = int(value)
                        else:
                            data[param] = value
            peak = re.sub("\s+", " ", paragraphs[2].prettify().replace('<p>', '').replace('</p>', '')).strip()
            peak_start, peak_end = self.extract_peak_dates(peak)
            data['peak_start'] = peak_start
            data['peak_end'] = peak_end

            showers.append(data)
        return showers

    def extract_peak_dates(self, peak):
        if match := re.search('peak on the (\w+) (\d+)-(\d+), (\d+) night', peak, re.IGNORECASE):
            month = match.group(1)
            date_from = match.group(2)
            date_to = match.group(3)
            date_year = match.group(4)
            peak_start = datetime.strptime(f"{month} {date_from} {date_year}", "%b %d %Y")
            peak_end = datetime.strptime(f"{month} {date_to} {date_year}", "%b %d %Y")
        else:
            peak_start = None
            peak_end = None
        return peak_start, peak_end

    def extract_date(self, str):
        DateFormat = "%B %d"
        if ',' in str:
            DateFormat += ", %Y"
        try:
            result = datetime.strptime(str, DateFormat)
        except:
            result = None
        return result


class MyTestCase(unittest.TestCase):
    def test_something(self):
        uut = ams()
        data = uut.parse()
        pprint(data)


if __name__ == '__main__':
    unittest.main()
