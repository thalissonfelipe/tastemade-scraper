
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
        """
        Normalize a string remove all non ascii code characters.

        @param str string: String to be normalized
        """

        nfkd_form = unicodedata.normalize('NFKD', string)
        only_ascii = nfkd_form.encode('ASCII', 'ignore')

        return only_ascii.decode('utf-8').replace(' ', '-')

    def get_categories(self) -> list[str]:
        """
        Returns a list of categories listed in the Tastemade website.
        """

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
        """
        Gets recipes basic information by category. This method returns a list
        of objects containing the image, name, category and path of the recipe
        to be later consulted to query all necessary information.

        @param str category: The category's name
        """

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
        names = set()

        for li in ul_li:
            url = li.find_element_by_tag_name('a').get_attribute('href')
            name = li.find_element_by_class_name(
                'MediaCard__Title-zlkxh-3').text
            image_url = self.get_url_from_selenium_element(li)

            # avoid duplicates
            if name in names:
                continue
            names.add(name)

            recipes.append({
                'url': url,
                'name': name,
                'category': category.split('-')[-1],
                'image_url': image_url
            })

        return recipes

    def scrap_recipes_data(self, data: list) -> list:
        """
        Scraps all informations of each recipe.

        @param list data: The list containing the url of each recipe.
        """

        for recipe in data:
            print(recipe['name'], '-', recipe['category'])
            self.driver.get(recipe['url'])

            # default values
            preparation_time = ''
            portions = ''
            cooking_time = ''
            ingredients = []
            instructions = []

            try:
                # get preparation time, portions or cooking time
                # @TODO refactor to another function
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

                # get ingredients as a list
                ul = self.driver.find_element_by_css_selector(
                    'ul.VideoRecipe__ColumnList-sc-4pl27p-4')
                ul_li_p = ul.find_elements_by_tag_name('p')
                ingredients = [p.text.strip() for p in ul_li_p]

                # get instructions as a list
                ol = self.driver.find_element_by_tag_name(
                    'ol.VideoRecipe__List-sc-4pl27p-5')
                ol_li_p = ol.find_elements_by_tag_name('p')
                instructions = [p.text.strip() for p in ol_li_p]
            except Exception:
                # if some items do not exist, just ignore
                pass

            recipe['preparation_time'] = preparation_time
            recipe['portions'] = portions
            recipe['cooking_time'] = cooking_time
            recipe['ingredients'] = ingredients
            recipe['instructions'] = instructions

        return data

    def get_recipes(self, output_path: str) -> list:
        """
        Gets all recipes.

        @param str output_path: Path to save the recipes.
        """

        data = []
        categories = self.get_categories()

        for category in categories:
            print(f'Recuperando informações basicas de {category}...')
            data.extend(self.scrap_recipes_basic_info_by_category(category))

        self.scrap_recipes_data(data)
        self.dump(output_path, data)
        self.driver.close()

        return data

    def filter_recipes(self, path: str, output: str) -> None:
        """
        Method to remove recipes that don't have an image url, ingredients or
        instructions.

        @param str path: Path to load de file
        @param str output: Path to the output file
        """

        data = self.load(path)

        for recipe in data[:]:
            if (
                recipe['image_url'] == 'none'
                or len(recipe['ingredients']) == 0
                or len(recipe['instructions']) == 0
            ):
                data.remove(recipe)

        self.dump(output, data)

    def dump(self, path: str, data: list) -> None:
        """
        Serialize an object as a JSON formatted stream.

        @param str path: Path to the output file
        @param str data: Object to be serialized
        """

        with open(path, 'w+') as outfile:
            json.dump(data, outfile)

    def load(self, path: str) -> list:
        """
        Serialized a JSON formatted stream to a Python object.

        @param str path: Path to the file to be loaded
        """

        data = None
        with open(path) as json_file:
            data = json.load(json_file)

        return data

    @staticmethod
    def get_url_from_selenium_element(element) -> str:
        """
        Helper method that retireves the image_url of each recipe.

        @param element: WebDriver element
        """

        background_image_raw = element.find_element_by_class_name(
            'LazyLoadDiv__LazyLoad-sc-1n0spl4-1'
        ).value_of_css_property('background-image')
        background_image = background_image_raw.split('?')[0].split('"')[-1]

        return background_image


if __name__ == '__main__':
    output_path = os.path.join(
        os.path.dirname(__file__), 'datasets', 'recipes.json')
    output_filtered_path = os.path.join(
        os.path.dirname(__file__), 'datasets', 'recipes_filtered.json')
    Scraper().get_recipes(output_path)
    Scraper().filter_recipes(output_path, output_filtered_path)
