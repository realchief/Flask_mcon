# coding: utf-8

from googletrans import Translator
from faker import Faker
faker = Faker('en-US')

number_messages = 3
headline_type = 'Unread'
message = 'Hey there, still wanna meet?'
name = 'Jennifer'

translations = [
    "ar",
    "bg",
    "ca",
    "cs",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "fa",
    "fi",
    "fr",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ka",
    "ko",
    "lt",
    "lv",
    "ms",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sr",
    "sv",
    "th",
    "tr",
    "uk",
    "vi"
]

localized_name_codes = {"ar": "ar_SA",
                        "bg": "bg_BG",
                        "ca": "es_ES",
                        "cs": "cs_CZ",
                        "da": "nl_NL",
                        "de": "de_DE",
                        "el": "el_GR",
                        "en": "en_US",
                        "es": "es_ES",
                        "et": "et_EE",
                        "fa": "fa_IR",
                        "fi": "fi_FI",
                        "fr": "fr_FR",
                        "hi": "hi_IN",
                        "hr": "hr_HR",
                        "hu": "hu_HU",
                        "id": "hi_IN",
                        "it": "it_IT",
                        "ja": "ja_JP",
                        "ka": "en_US",
                        "ko": "ko_KR",
                        "lt": "lt_LT",
                        "lv": "lv_LV",
                        "ms": "en_US",
                        "nl": "nl_NL",
                        "pl": "pl_PL",
                        "pt": "pt_PT",
                        "ro": "ro_RO",
                        "ru": "ru_RU",
                        "sk": "sl_SI",
                        "sr": "sl_SI",
                        "sv": "sv_SE",
                        "th": "en_US",
                        "tr": "tr_TR",
                        "uk": "uk_UA",
                        "vi": "en_US"
}
contents = {}
headings = {}
for translation in translations:
    print(translation)
    translator = Translator()
    fake = Faker(localized_name_codes[translation])
    name = fake.first_name_female()
    headline = "({}) {} messages from {}".format(number_messages, headline_type, name.encode("utf-8"))
    translated_headline = translator.translate('{}'.format(headline), src='en', dest='{}'.format(translation)).text
    contents[translation] = translated_headline
    translated_message = translator.translate('{}'.format(message), src='en', dest='{}'.format(translation)).text
    headings[translation] = translated_message

