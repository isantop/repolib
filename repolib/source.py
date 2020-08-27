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
"""

import os
from debian import deb822

from . import util

class SourceError(Exception):
    pass

class Source(deb822.Deb822):
    """ A Deb822 object representing a software source.

    Provides a dict-like interface for accessing and modifying DEB822-format
    sources, as well as options for loading and saving them from disk.
    """

    options_d = {
        'arch': 'Architectures',
        'lang': 'Languages',
        'target': 'Targets',
        'pdiffs': 'PDiffs',
        'by-hash': 'By-Hash'
    }


    def __init__(self, filename=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename

    def load_from_file(self, filename=None):
        """ Loads the data from a file path.

        Arguments:
            filename (str): The name of the file on disk.
        """
        if filename:
            self.filename = filename
        if not self.filename:
            raise SourceError("No filename to load from")

        full_path = util.sources_dir / filename

        with open(full_path, mode='r') as source_file:
            super().__init__(source_file)

    def save_to_disk(self):
        """ Saves the source to disk."""
        if not self.filename:
            raise SourceError('No filename to save to specified')
        full_path = util.sources_dir / self.filename

        with open(full_path, mode='w') as sources_file:
            sources_file.write(self.dump())

    def make_source_string(self):
        """ Makes a printable string of the source.

        This method is intended to provide output in a user-friendly format. For
        output representative of the actual data, use dump() instead.

        Returns:
            A str which can be printed to console.
        """
        if not self.name:
            self.name = self.filename.replace('.sources', '')

        toprint = self.dump()
        toprint = toprint.replace('X-Repolib-Name', 'Name')
        return toprint

    def set_source_enabled(self, enabled):
        """ Convenience method to set a source with source_code enabled.

        If source code is enabled, then the Types for self will be both
        BINARY and SOURCE. Otherwise it will be just BINARY.

        Arguments:
            enabled(bool): Wether or not to enable source-code.
        """
        if enabled:
            self.types = [util.AptSourceType.BINARY, util.AptSourceType.SOURCE]
        else:
            self.types = [util.AptSourceType.BINARY]


    @property
    def name(self):
        """ str: The name of the source."""
        try:
            return self['X-Repolib-Name']
        except KeyError:
            return None

    @name.setter
    def name(self, name):
        self['X-Repolib-Name'] = name

    @property
    def enabled(self):
        """ util.AptSourceEnabled: Whether the source is enabled or not. """
        try:
            return util.AptSourceEnabled(self['enabled'])
        except KeyError:
            return None

    @enabled.setter
    def enabled(self, enable):
        """ Accept a wide variety of data types/values for ease of use. """
        if enable in [True, 'Yes', 'yes', 'YES', 'y', 'Y', 1]:
            self['Enabled'] = util.AptSourceEnabled.TRUE.value
        else:
            self['Enabled'] = util.AptSourceEnabled.FALSE.value

    @property
    def types(self):
        """ list of util.AptSourceTypes: The types of packages provided. """
        try:
            types = []
            for dtype in self['Types'].split():
                types.append(util.AptSourceType(dtype.strip()))
            return types
        except KeyError:
            return None

    @types.setter
    def types(self, types):
        print(types)
        output_types = []
        for dtype in types:
            output_types.append(dtype.value)
        self['Types'] = ' '.join(output_types)


    @property
    def uris(self):
        """ [str]: The list of URIs providing packages. """
        try:
            return self['URIs'].split()
        except KeyError:
            return None

    @uris.setter
    def uris(self, uris):
        """ If the user tries to remove the last URI, disable as well. """
        if len(uris) > 0:
            self['URIs'] = ' '.join(uris)
        else:
            self['URIs'] = ''
            self.enabled = False

    @property
    def suites(self):
        """ [str]: The list of enabled Suites. """
        try:
            return self['Suites'].split()
        except KeyError:
            return None

    @suites.setter
    def suites(self, suites):
        """ If user removes the last suite, disable as well. """
        if len(suites) > 0:
            self['Suites'] = ' '.join(suites)
        else:
            self['Suites'] = ''
            self.enabled = False

    @property
    def components(self):
        """[str]: The list of components enabled. """
        try:
            return self['Components'].split()
        except KeyError:
            return None

    @components.setter
    def components(self, components):
        """ Also disable if the user tries to remove the last component. """
        if len(components) > 0:
            self['Components'] = ' '.join(components)
        else:
            self['Components'] = ''
            self.enabled = False

    @property
    def options(self):
        """ dict: Addtional options for the repository."""
        non_options = [
            'X-Repolib-Name', 'Enabled', 'Types', 'URIs', 'Suites', 'Components'
        ]
        options = {}
        for key in self:
            if key not in non_options:
                options[key] = self[key]
        if len(options) > 0:
            return options
        return None

    @options.setter
    def options(self, options):
        for key in options:
            self[key] = options[key]
