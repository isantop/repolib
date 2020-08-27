#!/usr/bin/python3

"""
Copyright (c) 2019-2020, Ian Santopietro
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This is a library for parsing deb lines into deb822-format data.
"""

import unittest

from . import deb
from . import util

class DebTestCase(unittest.TestCase):
    def test_normal_source(self):
        source = deb.DebLine(
            'deb http://example.com/ suite main'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertEqual(source.types, [util.AptSourceType.BINARY])
        self.assertTrue(source.enabled.get_bool())
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertEqual(source.suites, ['suite'])
        self.assertEqual(source.components, ['main'])
        self.assertIsNone(source.options)
        self.assertEqual(source.filename, 'deb-example-com.sources')
    
    def test_source_with_multiple_components(self):
        source = deb.DebLine(
            'deb http://example.com/ suite main nonfree'
        )
        self.assertEqual(source.suites, ['suite'])
        self.assertEqual(source.components, ['main', 'nonfree'])
    
    def test_source_with_option(self):
        source = deb.DebLine(
            'deb [ arch=amd64 ] http://example.com/ suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertDictEqual(source.options, {'Architectures': 'amd64'})
    
    def test_source_uri_with_brackets(self):
        source = deb.DebLine(
            'deb http://example.com/[release]/ubuntu suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/[release]/ubuntu'])
        self.assertIsNone(source.options, {})
    
    def test_source_options_with_colons(self):
        source = deb.DebLine(
            'deb [ arch=arm:2 ] http://example.com/ suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertDictEqual(source.options, {'Architectures': 'arm:2'})
    
    def test_source_with_multiple_option_values(self):
        source = deb.DebLine(
            'deb [ arch=armel,amd64 ] http://example.com/ suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertDictEqual(source.options, {'Architectures': 'armel amd64'})
    
    def test_source_with_multiple_options(self):
        source = deb.DebLine(
            'deb [ arch=amd64 lang=en_US ] http://example.com/ suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertDictEqual(
            source.options, 
            {'Architectures': 'amd64', 'Languages': 'en_US'}
        )
    
    def test_source_with_multiple_options_with_multiple_values(self):
        source = deb.DebLine(
            'deb [ arch=amd64,armel lang=en_US,en_CA ] http://example.com/ suite main'
        )
        self.assertEqual(source.uris, ['http://example.com/'])
        self.assertDictEqual(
            source.options, 
            {'Architectures': 'amd64 armel', 'Languages': 'en_US en_CA'}
        )
    
    def test_source_uri_with_brackets_and_options(self):
        source = deb.DebLine(
            'deb [ arch=amd64 lang=en_US,en_CA ] http://example][.com/[release]/ubuntu suite main'
        )
        self.assertEqual(source.uris, ['http://example][.com/[release]/ubuntu'])
        self.assertDictEqual(
            source.options, 
            {'Architectures': 'amd64', 'Languages': 'en_US en_CA'}
        )
    
    def test_source_uri_with_brackets_and_options_with_colons(self):
        source = deb.DebLine(
            'deb [ arch=amd64,arm:2 lang=en_US,en_CA ] http://example][.com/[release]/ubuntu suite main'
        )
        self.assertEqual(source.uris, ['http://example][.com/[release]/ubuntu'])
        self.assertDictEqual(
            source.options, 
            {'Architectures': 'amd64 arm:2', 'Languages': 'en_US en_CA'}
        )
    
    def test_worst_case_sourcenario(self):
        source = deb.DebLine(
            'deb [ arch=amd64,arm:2,arm][ lang=en_US,en_CA ] http://example][.com/[release:good]/ubuntu suite main restricted nonfree not-a-component'
        )
        self.assertEqual(source.uris, ['http://example][.com/[release:good]/ubuntu'])
        self.assertEqual(source.suites, ['suite'])
        self.assertEqual(source.components, [
            'main', 'restricted', 'nonfree', 'not-a-component'
        ])
        self.assertDictEqual(
            source.options, 
            {
                'Architectures': 'amd64 arm:2 arm][', 
                'Languages': 'en_US en_CA'
            }
        )
    
    def test_source_code_source(self):
        source = deb.DebLine(
            'deb-src http://example.com/ suite main'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertEqual(source.types, [util.AptSourceType.SOURCE])
    
    def test_disabled_source(self):
        source = deb.DebLine(
            '# deb http://example.com/ suite main'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertFalse(source.enabled.get_bool())
    
    def test_disabled_source_without_space(self):
        source = deb.DebLine(
            '#deb http://example.com/ suite main'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertFalse(source.enabled.get_bool())
    
    def test_source_with_trailing_comment(self):
        source = deb.DebLine(
            'deb http://example.com/ suite main # This is a comment'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertEqual(source.suites, ['suite'])
        self.assertEqual(source.components, ['main'])
    
    def test_disabled_source_with_trailing_comment(self):
        source = deb.DebLine(
            '# deb http://example.com/ suite main # This is a comment'
        )
        self.assertEqual(source.name, 'deb-example-com')
        self.assertEqual(source.suites, ['suite'])
        self.assertFalse(source.enabled.get_bool())
        self.assertEqual(source.components, ['main'])
    
    @unittest.expectedFailure
    def test_cdrom_source(self):
        source = deb.DebLine(
            '# deb cdrom:[This is a CD-ROM Source] suite main # This is a comment'
        )
        self.assertEqual(source.uris, ['cdrom:[This is a CD-ROM Source]'])
