import pytest

from asphalt.web.request import HTTPAccept, HTTPAcceptLanguage


class TestHTTPAccept:
    @pytest.mark.parametrize('header, available, expected', [
        ('da, en-gb;q=0.8, en;q=0.7', ['fi', 'en'], 'en'),
        ('da, en-gb;q=0.8, en;q=0.7', ['da', 'en'], 'da'),
        ('da, en-gb;q=0.8, en;q=0.7', [], 'fb'),
        ('da, en-gb;q=0.8, en;q=0.7, *;q=0.5', ['en-us'], 'en-us'),
        (None, ['da', 'en-us'], 'da'),
        (None, [], 'fb')
    ])
    def test_best_match(self, header, available, expected):
        accept = HTTPAcceptLanguage(header)
        assert accept.best_match(available, 'fb') == expected

    def test_repr(self):
        accept = HTTPAccept('da;q=1, en-gb;q=0.812, en;q=0.7, *;q=0.53')
        assert repr(accept) == "HTTPAccept('da, en-gb;q=0.812, en;q=0.7, *;q=0.53')"


class TestHTTPAcceptLanguage:
    @pytest.mark.parametrize('header, available, expected', [
        ('da, en-gb;q=0.8, en;q=0.7', ['fi', 'en'], 'en'),
        ('da, en-gb;q=0.8, en;q=0.7', ['da', 'en'], 'da'),
        ('da, en-gb;q=0.8, en;q=0.7', [], 'fb'),
        ('da, en-gb;q=0.8, en;q=0.7, *;q=0.5', ['en-us'], 'en-us'),
        (None, ['da', 'en-us'], 'da'),
        (None, [], 'fb')
    ])
    def test_best_match(self, header, available, expected):
        accept = HTTPAcceptLanguage(header)
        assert accept.best_match(available, 'fb') == expected

    def test_repr(self):
        accept = HTTPAcceptLanguage('da;q=1, en-gb;q=0.812, en;q=0.7, *;q=0.53')
        assert repr(accept) == "HTTPAcceptLanguage('da, en-gb;q=0.812, en;q=0.7, *;q=0.53')"
