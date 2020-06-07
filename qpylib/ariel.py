#!/usr/bin/python
# Licensed Materials - Property of IBM
# 5725I76-CC011829
# (C) Copyright IBM Corp. 2012, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import time
import logging
from flask import request
from . import qpylib

class ArielSearchError(Exception):
    """Exception raised for errors in Ariel search.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        super(ArielSearchError, self).__init__(message)
        self.expression = expression
        self.message = message
    def __str__(self):
        return self.message
class ArielSearches():
    """ Provides methods for executing Ariel searches from the QRadar ariel API."""

    def __init__(self, auth_token=None):
        """Constructor."""
        self.logger = logging.getLogger('com.ibm.applicationLogger')
        self.auth_token = auth_token

    @staticmethod
    def __acquire_sec_token():
        """
            Acquire security token
        """
        if request:
            return request.cookies.get('SEC')
        return None

    @staticmethod
    def __acquire_qradarcsrf_token():
        """
         Acquire QRadar CSRF token
        """
        if request:
            return request.cookies.get('QRadarCSRF')
        return None

    def get_tokens(self, headers):
        """
         Retrieve tokens
        """
        if headers is None:
            headers = {}
        if 'SEC' not in headers:
            if self.auth_token:
                headers['SEC'] = self.auth_token
            elif request:
                sec = self.__acquire_sec_token()
                headers['SEC'] = self.__acquire_sec_token()
            else:
                raise ArielSearchError(None, "Unable to aquire any SEC token")
        if request and 'QRadarCSRF' not in headers:
            headers['QRadarCSRF'] = self.__acquire_qradarcsrf_token()
        return headers

    def search(self, query):
        """ Creates an Ariel search as specified by the AQL query expression.
        Searches are performed asynchronously.
        @param query: The AQL query to execute.
        @return: Tuple containing the search status and search_id.
        """
        headers = self.get_tokens({'Accept':'application/json', 'Content-Type':'application/json',
                                   'Version':'5.1'})
        params = {'query_expression':query, 'fields':'status,search_id'}
        full_url = 'api/ariel/searches'
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("REQUEST: {%s}, headers={%s}, params={%s}",
                              full_url, headers, params)
        response = qpylib.REST('post', full_url, headers=headers, params=params)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("RESPONSE (status_code={%d}): {%s}",
                              response.status_code, response.text)
        if response.status_code != 201:
            self.logger.error(str(response.status_code) + " Failed to start Ariel search with query expression {%s}: {%s}",
                              query, response.text)
            try:
                response_json = response.json()
                message = response_json["message"] if "message" in response_json else response.text
            except ValueError:
                message = response.text
            raise ArielSearchError(query, message)
        return (response.json().get('status'), response.json().get('search_id'))

    def search_s(self, query, timeout=60):
        """ Creates an Ariel search as specified by the AQL query expression.
        Searches are performed synchronously.
        @param query: The AQL query to execute.
        @param timeout: The timeout to wait for the search to complete
        @return: The record count of the search results.
        """
        response = self.search(query)
        wait_timeout = time.time() + timeout
        search_id = response[1]
        while True:
            status, record_count = self.status(search_id)
            if status in ('CANCELED', 'ERROR'):
                raise ArielSearchError(query,
                                       "Ariel search_id {0} failed; {1}"
                                       .format(search_id, status))
            if status == 'COMPLETED':
                return (search_id, record_count)

            if time.time() < wait_timeout:
                time.sleep(10)
                continue
            raise ArielSearchError(query,
                                   "Ariel search_id {0} did not complete within {1}s!"
                                   .format(search_id, timeout))

    def status(self, search_id):
        """Retrieve status information for a search, based on the search_id parameter.
        @param search_id: The identifier for an Ariel search.
        @return: Tuple containing the search status and record count.
        """
        headers = self.get_tokens({'Accept':'application/json', 'Content-Type':'application/json',
                                   'Version':'5.1'})
        params = {'fields': 'status,record_count'}
        full_url = 'api/ariel/searches/' + search_id
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("REQUEST: {%s}, headers={%s},params={%s}",
                              full_url, headers, params)
        response = qpylib.REST('get', full_url, headers=headers, params=params)
        response_json = response.json()
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("RESPONSE: {%s}", response_json)
        if response.status_code != 200:
            raise ArielSearchError(None, "Ariel search_id {0} failed;{1}"
                                   .format(search_id, response.content))
        return (response_json['status'], response_json['record_count'])

    def results(self, search_id, start=0, end=0):
        """ Retrieve the results of the Ariel search that is identified by the search_id.
        @param search_id: The identifier for an Ariel search.
        @param start: the start offset of the range of records to return
        @param end: the end offset of the range of records to return
        """
        headers = self.get_tokens({'Accept':'application/json', 'Content-Type':'application/json',
                                   'Version':'5.1'})
        if (start < 0) or (end < start):
            raise ValueError("Invalid range; the results are indexed starting at zero")
        if end > 0:
            headers['Range'] = 'items={0}-{1}'.format(start, end)
        full_url = 'api/ariel/searches/{0}/results'.format(search_id)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("REQUEST: {%s}, headers={%s}, params=",
                              full_url, headers)
        response = qpylib.REST('get', full_url, headers=headers)
        if response.status_code != 200:
            raise ArielSearchError(None, "Ariel search {0} failed; {1}"
                                   .format(search_id, response.content))
        return response.json()
