import logging
import re
from tldextract import extract

logger = logging.getLogger('spacel.security.acm')


class AcmCertificates(object):
    def __init__(self, clients):
        self._clients = clients

    def get_certificate(self, region, hostname):
        logger.debug('Looking up certificate for "%s".', hostname)

        host_wildcards = self._get_wildcards(hostname)
        logger.debug('Resolved wildcards: %s', host_wildcards)
        acm = self._clients.acm(region)

        wildcard_cert = None
        wildcard_count = 100

        # Iterate certificates:
        for acm_cert in self._get_certificates(acm):
            cert_domain = acm_cert['DomainName']
            cert_arn = acm_cert['CertificateArn']

            # Stop search if exact match is found:
            if cert_domain == hostname:
                logger.debug('Found exact match for "%s": %s"', hostname,
                             cert_arn)
                return cert_arn

            if cert_domain in host_wildcards:
                star_count = cert_domain.count('*')
                if star_count < wildcard_count:
                    wildcard_count = star_count
                    wildcard_cert = cert_arn

        if wildcard_cert:
            logger.debug('Found wildcard match for "%s": %s (%s)', hostname,
                         wildcard_cert, wildcard_count)
        return wildcard_cert

    @staticmethod
    def _get_wildcards(hostname):
        extracted = extract('http://%s' % hostname)
        if not extracted.subdomain:
            return []

        common_domain = [extracted.domain, extracted.suffix]

        wildcards = []
        # For each subdomain component:
        split_subdomain = extracted.subdomain.split('.')
        for i in range(len(split_subdomain)):
            # Replace with wildcard, then concat to remaining bits:
            wildcard_parts = ['*'] * (i + 1) + split_subdomain[i + 1:]
            wildcard_parts += common_domain
            wildcards.append('.'.join(wildcard_parts))

        return wildcards

    @staticmethod
    def _get_certificates(acm):
        certificate_pages = (acm.get_paginator('list_certificates')
                             .paginate(CertificateStatuses=['ISSUED']))

        for certificate_page in certificate_pages:
            for certificate in certificate_page['CertificateSummaryList']:
                yield certificate
