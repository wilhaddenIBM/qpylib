# Copyright 2019 IBM Corporation All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=redefined-outer-name, unused-argument, invalid-name

import os
import json
import pytest
import responses
from qpylib.ariel import ArielSearches, ArielSearchError

login_count_query = '''
                        select username, count(*) from events
                        where qid=28250025  and NOT ( INCIDR('169.254.0.0/16',sourceip) )
                        and NOT (username in ('configservices', 'nobody', 'root'))
                        group by username last 7 DAYS
                        '''
@pytest.fixture()
def env_qradar_console_fqdn():
    os.environ['QRADAR_CONSOLE_FQDN'] = 'myhost.ibm.com'
    yield
    del os.environ['QRADAR_CONSOLE_FQDN']

@responses.activate
def test_fails_when_no_sec_token_supplied(env_qradar_console_fqdn):
    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json={'success': True}, status=200)
    ariel = ArielSearches()
    with pytest.raises(ArielSearchError, match='Unable to aquire any SEC token'):
        cursor_id = ariel.search_s('', 300)

@responses.activate
def test_search_failure(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'WAIT'
    ret_obj['record_count'] = '0'
    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'COMPLETED'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=400)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    with pytest.raises(ArielSearchError, match='failed'):
         ariel.search_s(login_count_query, timeout=0)

@responses.activate
def test_timeout_query(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'POOP'
    ret_obj['record_count'] = '0'
    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'TOOT'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    with pytest.raises(ArielSearchError, match='did not complete within'):
         ariel.search_s(login_count_query, timeout=0)

@responses.activate
def test_errored_query(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'ERROR'
    ret_obj['record_count'] = '0'
    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'ERROR'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    with pytest.raises(ArielSearchError, match='failed'):
         ariel.search_s(login_count_query)

@responses.activate
def test_cancelled_query(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'CANCELED'
    ret_obj['record_count'] = '0'
    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'CANCELED'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)


    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    with pytest.raises(ArielSearchError, match='failed'):
         ariel.search_s(login_count_query)

@responses.activate
def test_simple_query(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'WAIT'
    ret_obj['record_count'] = '0'

    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'COMPLETED'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)

    result = {} 
    result['username'] = "admin"
    result['COUNT'] = "1"
    results = {}
    results['events'] = [result]
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c/results',
                  json=results, status=200)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    cursor_id = ariel.search_s(login_count_query, 300)
    login_response = ariel.results(cursor_id[0])['events']
    
    print ( str(login_response) , file=open("/tmp/output.txt", "w"))
    for obj in login_response:
        assert obj['username'] == "admin"
        assert obj['COUNT'] == "1"

@responses.activate
def test_end_after_start_fails(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'WAIT'
    ret_obj['record_count'] = '0'

    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'COMPLETED'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)

    result = {} 
    result['username'] = "admin"
    result['COUNT'] = "1"
    results = {}
    results['events'] = [result]
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c/results',
                  json=results, status=200)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    cursor_id = ariel.search_s(login_count_query, 300)
    with pytest.raises(ValueError, match='Invalid range; the results are indexed starting at zero'):
        ariel.results(cursor_id[0], start=1)

@responses.activate
def test_status_failed_fails(env_qradar_console_fqdn):
    ret_obj = {}
    ret_obj['cursor_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['search_id'] = 'fa7a12c4-a3a7-425a-82b3-67d42c33860c'
    ret_obj['status'] = 'WAIT'
    ret_obj['record_count'] = '0'

    responses.add('POST', 'https://myhost.ibm.com/api/ariel/searches',
                  json=ret_obj, status=201)

    ret_obj['status'] = 'COMPLETED'
    ret_obj['record_count'] = '1'
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c?fields=status%2Crecord_count',
                  json=ret_obj, status=200)

    result = {} 
    result['username'] = "admin"
    result['COUNT'] = "1"
    results = {}
    results['events'] = [result]
    responses.add('GET', 'https://myhost.ibm.com/api/ariel/searches/fa7a12c4-a3a7-425a-82b3-67d42c33860c/results',
                  json=results, status=300)

    ariel = ArielSearches("l_o_n_g_w_a_v_e")
    cursor_id = ariel.search_s(login_count_query, 300)
    with pytest.raises(ArielSearchError, match='failed'):
        ariel.results(cursor_id[0], end=1)
