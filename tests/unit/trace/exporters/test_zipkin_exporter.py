# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import mock

from opencensus.trace import span_context
from opencensus.trace import span_data as span_data_module
from opencensus.trace.exporters import zipkin_exporter


class TestZipkinExporter(unittest.TestCase):
    def test_constructor(self):
        service_name = 'my_service'
        host_name = '0.0.0.0'
        port = 2333
        endpoint = '/api/v2/test'
        ipv4 = '127.0.0.1'

        exporter = zipkin_exporter.ZipkinExporter(
            service_name=service_name,
            host_name=host_name,
            port=port,
            endpoint=endpoint,
            ipv4=ipv4)

        expected_url = 'http://0.0.0.0:2333/api/v2/test'

        self.assertEqual(exporter.service_name, service_name)
        self.assertEqual(exporter.host_name, host_name)
        self.assertEqual(exporter.port, port)
        self.assertEqual(exporter.endpoint, endpoint)
        self.assertEqual(exporter.url, expected_url)
        self.assertEqual(exporter.ipv4, ipv4)

    def test_export(self):
        exporter = zipkin_exporter.ZipkinExporter(
            service_name='my_service', transport=MockTransport)
        exporter.export({})

        self.assertTrue(exporter.transport.export_called)

    @mock.patch('requests.post')
    @mock.patch.object(zipkin_exporter.ZipkinExporter,
                       'translate_to_zipkin')
    def test_emit_succeeded(self, translate_mock, requests_mock):
        import json

        trace = {'test': 'this_is_for_test'}

        exporter = zipkin_exporter.ZipkinExporter(service_name='my_service')
        response = mock.Mock()
        response.status_code = 202
        requests_mock.return_value = response
        translate_mock.return_value = trace
        exporter.emit([])

        requests_mock.assert_called_once_with(
            url=exporter.url,
            data=json.dumps(trace),
            headers=zipkin_exporter.ZIPKIN_HEADERS)

    @mock.patch('requests.post')
    @mock.patch.object(zipkin_exporter.ZipkinExporter,
                       'translate_to_zipkin')
    def test_emit_failed(self, translate_mock, requests_mock):
        import json

        trace = {'test': 'this_is_for_test'}

        exporter = zipkin_exporter.ZipkinExporter(service_name='my_service')
        response = mock.Mock()
        response.status_code = 400
        requests_mock.return_value = response
        translate_mock.return_value = trace
        exporter.emit([])

        requests_mock.assert_called_once_with(
            url=exporter.url,
            data=json.dumps(trace),
            headers=zipkin_exporter.ZIPKIN_HEADERS)

    def test_translate_to_zipkin_span_kind_none(self):
        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        spans_ipv4 = [
            span_data_module.SpanData(
                name='child_span',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id='6e0c63257de34c92',
                parent_span_id='6e0c63257de34c93',
                attributes={'test_key': 'test_value'},
                start_time='2017-08-15T18:02:26.071158Z',
                end_time='2017-08-15T18:02:36.071158Z',
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=0,
            ),
            span_data_module.SpanData(
                name='child_span',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id='6e0c63257de34c92',
                parent_span_id='6e0c63257de34c93',
                attributes={'test_key': 1},
                start_time='2017-08-15T18:02:26.071158Z',
                end_time='2017-08-15T18:02:36.071158Z',
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=None,
            ),
        ]

        trace_id = '6e0c63257de34c92bf9efcd03927272e'
        spans_ipv6 = [
            span_data_module.SpanData(
                name='child_span',
                context=span_context.SpanContext(trace_id=trace_id),
                span_id='6e0c63257de34c92',
                parent_span_id=None,
                attributes={
                    'test_key': False,
                    'test_key2': 'raw_value',
                    # these tags are malformed and should be omitted
                    'test_key3': 0.1,
                },
                start_time='2017-08-15T18:02:26.071158Z',
                end_time='2017-08-15T18:02:36.071158Z',
                child_span_count=None,
                stack_trace=None,
                time_events=None,
                links=None,
                status=None,
                same_process_as_parent_span=None,
                span_kind=1,
            ),
        ]

        ipv4 = '127.0.0.1'
        ipv6 = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'

        local_endpoint_ipv4 = {
            'serviceName': 'my_service',
            'ipv4': ipv4,
            'port': 9411,
        }

        local_endpoint_ipv6 = {
            'serviceName': 'my_service',
            'ipv6': ipv6,
            'port': 9411,
        }

        expected_zipkin_spans_ipv4 = [
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '6e0c63257de34c92',
                'parentId': '6e0c63257de34c93',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint_ipv4,
                'tags': {'test_key': 'test_value'},
            },
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '6e0c63257de34c92',
                'parentId': '6e0c63257de34c93',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint_ipv4,
                'tags': {'test_key': '1'},
            },
        ]

        expected_zipkin_spans_ipv6 = [
            {
                'traceId': '6e0c63257de34c92bf9efcd03927272e',
                'id': '6e0c63257de34c92',
                'name': 'child_span',
                'timestamp': 1502820146000000,
                'duration': 10000000,
                'localEndpoint': local_endpoint_ipv6,
                'tags': {'test_key': 'False', 'test_key2': 'raw_value'},
                'kind': 'SERVER',
            },
        ]

        # Test ipv4 local endpoint
        exporter_ipv4 = zipkin_exporter.ZipkinExporter(
            service_name='my_service', ipv4=ipv4)
        ipv4_trace = span_data_module.format_legacy_trace_json(spans_ipv4)
        zipkin_spans_ipv4 = exporter_ipv4.translate_to_zipkin(
            trace_id=trace_id,
            spans=ipv4_trace.get('spans'))

        self.assertEqual(zipkin_spans_ipv4, expected_zipkin_spans_ipv4)

        # Test ipv6 local endpoint
        exporter_ipv6 = zipkin_exporter.ZipkinExporter(
            service_name='my_service', ipv6=ipv6)
        ipv6_trace = span_data_module.format_legacy_trace_json(spans_ipv6)
        zipkin_spans_ipv6 = exporter_ipv6.translate_to_zipkin(
            trace_id=trace_id,
            spans=ipv6_trace.get('spans')
        )

        self.assertEqual(zipkin_spans_ipv6, expected_zipkin_spans_ipv6)

    def test_ignore_incorrect_spans(self):
        span1 = {
            'attributes': {
                'attributeMap': {
                    'float_value': {
                        'value': 0.1
                    }
                }
            }
        }
        self.assertEqual(zipkin_exporter._extract_tags_from_span(span1), {})

        span2 = {
            'attributes': {
                'attributeMap': {
                    'bool_value': False
                }

            }
        }
        self.assertEqual(zipkin_exporter._extract_tags_from_span(span2), {})


class MockTransport(object):
    def __init__(self, exporter=None):
        self.export_called = False
        self.exporter = exporter

    def export(self, trace):
        self.export_called = True
