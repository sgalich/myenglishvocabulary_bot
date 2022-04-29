from texts import en#, ru

DEFAULT_LANGUAGE_CODE = 'en'


def get(language_code: str) -> en:
    """Return a language module by its name."""
    try:
        answer = globals()[language_code]
        print(answer)
        return answer
    except Exception as e:
        print('error')
        print(e)
        return globals()[DEFAULT_LANGUAGE_CODE]
    # print([globals()[language_code]])
    # return globals()[language_code]
