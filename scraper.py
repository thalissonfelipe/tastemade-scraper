
import os
import json
import unicodedata
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Scraper:
    BASE_URL = 'https://www.tastemade.com.br/receitas'
    CHROMEDRIVER_PATH = os.path.join(
        os.path.dirname(__file__), 'drivers', 'chromedriver')
    OUTPUT_PATH = os.path.join(
        os.path.dirname(__file__), 'datasets', 'recipes.json')
    OUTPUT_FILTERED_PATH = os.path.join(
        os.path.dirname(__file__), 'datasets', 'recipes_filtered.json')

    def __init__(self) -> None:
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(
            executable_path=self.CHROMEDRIVER_PATH,
            options=options
        )
        self.driver.get(self.BASE_URL)

    @staticmethod
    def normalize_string(string: str) -> str:
        nfkd_form = unicodedata.normalize('NFKD', string)
        only_ascii = nfkd_form.encode('ASCII', 'ignore')

        return only_ascii.decode('utf-8').replace(' ', '-')

    def get_categories(self) -> list[str]:
        ul = self.driver.find_element_by_xpath(
            '//*[@id="react-root"]/div[2]/div/div/ul[1]')
        ul_li = ul.find_elements_by_tag_name('li')
        ul_li.pop(len(ul_li)-1)
        categories = []

        for li in ul_li:
            category = li.find_elements_by_tag_name('a')[-1].text
            categories.append(self.normalize_string(category))

        return categories

    def scrap_recipes_basic_info_by_category(self, category: str) -> list:
        self.driver.get(f'{self.BASE_URL}/{category}')

        try:
            button_xpath = '//*[@id="react-root"]/div[2]/button'
            button = self.driver.find_element_by_xpath(button_xpath)
            while button:
                button.click()
                button = self.driver.find_element_by_xpath(button_xpath)
                sleep(1)
        except Exception:
            pass

        ul = self.driver.find_element_by_xpath(
            '//*[@id="react-root"]/div[2]/div/div/ul')
        ul_li = ul.find_elements_by_tag_name('li')
        recipes = []

        for li in ul_li:
            url = li.find_element_by_tag_name('a').get_attribute('href')
            name = li.find_element_by_class_name(
                'MediaCard__Title-zlkxh-3').text
            image_url = self.get_url_from_selenium_element(li)

            recipes.append({
                'url': url,
                'name': name,
                'image_url': image_url
            })

        return recipes

    def scrap_recipes_data(self, data: dict) -> dict:
        for key, recipes in data.items():
            print(f'Recuperando {key}...')
            for index, recipe in enumerate(recipes):
                self.driver.get(recipe['url'])

                # default values
                preparation_time = ''
                portions = ''
                cooking_time = ''
                ingredients = []
                instructions = []

                try:
                    divs = self.driver.find_elements_by_class_name(
                        'VideoRecipe__InfoItem-sc-4pl27p-2')

                    for div in divs:
                        span = div.find_element_by_tag_name('span')
                        span_text = span.text.strip(':').lower()
                        p = div.find_element_by_tag_name('p').text.strip()
                        if span_text == 'preparação':
                            preparation_time = p
                        elif span_text == 'porções':
                            portions = p
                        elif span_text == 'cozimento':
                            cooking_time = p

                    ingredients = self.driver.find_elements_by_class_name(
                        'p-ingredient')
                    ingredients = [i.text.strip() for i in ingredients]
                    ol = self.driver.find_element_by_tag_name('ol')
                    ol_li_p = ol.find_elements_by_tag_name('p')
                    instructions = [p.text.strip() for p in ol_li_p]
                except Exception:
                    pass

                data[key][index]['preparation_time'] = preparation_time
                data[key][index]['portions'] = portions
                data[key][index]['cooking_time'] = cooking_time
                data[key][index]['ingredients'] = ingredients
                data[key][index]['instructions'] = instructions

        return data

    def get_recipes(self) -> dict:
        data = {}
        categories = self.get_categories()

        for category in categories:
            print(f'Recuperando informações basicas de {category}...')
            data[category] = \
                self.scrap_recipes_basic_info_by_category(category)

        data = self.scrap_recipes_data(data)

        self.dump(self.OUTPUT_PATH, data)
        self.driver.close()

        return data

    def filter_json(self) -> None:
        data = self.load()

        for key, recipes in data.items():
            for recipe in recipes[:]:
                if (
                    recipe['image_url'] == 'none'
                    or len(recipe['ingredients']) == 0
                    or len(recipe['instructions']) == 0
                ):
                    recipes.remove(recipe)
            data[key] = recipes

        self.dump(self.OUTPUT_FILTERED_PATH, data)

    def dump(self, path: str, data: dict) -> None:
        with open(path, 'w+') as outfile:
            json.dump(data, outfile)

    def load(self) -> dict:
        data = None
        with open(self.OUTPUT_PATH) as json_file:
            data = json.load(json_file)

        return data

    @staticmethod
    def get_url_from_selenium_element(element) -> str:
        background_image_raw = element.find_element_by_class_name(
            'LazyLoadDiv__LazyLoad-sc-1n0spl4-1'
        ).value_of_css_property('background-image')
        background_image = background_image_raw.split('?')[0].split('"')[-1]

        return background_image


if __name__ == '__main__':
    Scraper().filter_json()
