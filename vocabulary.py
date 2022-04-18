import eng_to_ipa
import requests
import scrapy
from PyDictionary import PyDictionary

dictionary = PyDictionary()


def get_definition(word: str) -> str:
    """Get definition of the word."""
    first_word = word.split()[0]    # Leave only 1st word
    url = f'http://wordnetweb.princeton.edu/perl/webwn?s={first_word}'
    definition = ""
    response = requests.get(url).text
    response = scrapy.selector.Selector(text=response)
    parts_of_speech = response.xpath('//h3/text()').getall()
    for part_of_speech in parts_of_speech:
        definition += f'\n\n{part_of_speech}'
        all_definitions_xpath = f'//h3[text()="{part_of_speech}"]/following-sibling::ul//li/text()'
        all_definitions = response.xpath(all_definitions_xpath).getall()
        all_definitions = [x.strip(', ').strip().replace('(', '', 1) \
            [::-1].replace(')', '', 1)[::-1] for x in all_definitions]
        # Shorten definitions
        # Otherwise the message is too long: telegram.error.BadRequest: Message_too_long
        all_definitions = [x for x in all_definitions if x][:3]
        for definition_var in all_definitions:
            definition += f'\n\t– {definition_var}'
    definition = definition.strip()
    return definition


def get_pronunciation(word: str) -> str:
    pronunciation = eng_to_ipa.convert(''.join(word))
    return pronunciation


def get_synonyms(word: str) -> str:
    first_word = word.split()[0]  # Leave only 1st word
    synonyms = dictionary.synonym(first_word)
    synonyms = ', '.join(synonyms[:10]) if synonyms else ''
    return synonyms
