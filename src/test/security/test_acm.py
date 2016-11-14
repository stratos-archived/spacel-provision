from mock import MagicMock
import unittest

from spacel.aws import ClientCache
from spacel.security.acm import AcmCertificates
from test import ORBIT_REGION

TEST_EXAMPLE_COM = '111111'
STAR_EXAMPLE_COM = '222222'
STAR_TEST_DOUBLE_COM = '333333'
STAR_STAR_DOUBLE_COM = '444444'

CERTIFICATE_LIST = [
    {'DomainName': 'test.example.com', 'CertificateArn': TEST_EXAMPLE_COM},
    {'DomainName': '*.example.com', 'CertificateArn': STAR_EXAMPLE_COM},
    {'DomainName': '*.test.double.com', 'CertificateArn': STAR_TEST_DOUBLE_COM},
    {'DomainName': '*.*.double.com', 'CertificateArn': STAR_STAR_DOUBLE_COM}
]


class TestAcmCertificates(unittest.TestCase):
    def setUp(self):
        self.acm = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.acm_certs = AcmCertificates(self.clients)

    def test_get_wildcards(self):
        wildcards = self.acm_certs._get_wildcards('foo.bar.com')
        self.assertEquals(['*.bar.com'], wildcards)

    def test_get_wildcards_none(self):
        wildcards = self.acm_certs._get_wildcards('bar.com')
        self.assertEquals([], wildcards)

    def test_get_wildcards_subdomains(self):
        wildcards = self.acm_certs._get_wildcards('baz.foo.bar.com')
        self.assertEquals([
            '*.foo.bar.com',
            '*.*.bar.com'
        ], wildcards)

    def test_get_certificates(self):
        paginator = MagicMock()

        paginator.paginate.return_value = [{
            'CertificateSummaryList': CERTIFICATE_LIST
        }, {
            'CertificateSummaryList': CERTIFICATE_LIST
        }]
        self.acm.get_paginator.return_value = paginator

        certificates = [c for c in self.acm_certs._get_certificates(self.acm)]
        self.assertEquals(8, len(certificates))

    def test_get_certificate_exact(self):
        self._mock_certs()
        cert = self.acm_certs.get_certificate(ORBIT_REGION, 'test.example.com')
        self.assertEquals(cert, TEST_EXAMPLE_COM)

    def test_get_certificate_wildcard(self):
        self._mock_certs()
        cert = self.acm_certs.get_certificate(ORBIT_REGION, 'other.example.com')
        self.assertEquals(cert, STAR_EXAMPLE_COM)

    def test_get_certificate_best_wildcard(self):
        self._mock_certs()
        cert = self.acm_certs.get_certificate(ORBIT_REGION, 'test.test.double.com')
        # Both STAR_STAR and STAR_TEST will work, we want the most specific:
        self.assertEquals(cert, STAR_TEST_DOUBLE_COM)

    def _mock_certs(self):
        self.acm_certs._get_certificates = MagicMock(
            return_value=CERTIFICATE_LIST)
