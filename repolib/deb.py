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
# pylint: disable=too-many-ancestors, too-many-instance-attributes
# If we want to use the subclass, we don't have a lot of options.

from . import source
from . import util

class DebLineSourceException(Exception):
    """ Exceptions with DebLine Sources. """

    def __init__(self, *args, code=1, **kwargs):
        """Exception with a debline source object

        Arguments:
            code (:obj:`int`, optional, default=1): Exception error code.
    """
        super().__init__(*args, **kwargs)
        self.code = code

class DebLine(source.Source):
    """ Sources input via a deb line. """

    def __init__(self, line):
        super().__init__()

        self.deb_line = line
        if 'cdrom:' in self.deb_line:
            raise DebLineSourceException(
                'RepoLib does not support \'cdrom:\' URIs via this DebLine Class. '
                'Please use a Source() class to add these sources'
            )
        self._parse_debline(self.deb_line)
        self.filename = self.make_name(prefix="deb-")
        self.name = self.filename.replace('.sources', '')

    def copy(self, source_code=True):
        """ Copies the source and returns an identical source object.

        Arguments:
            source_code (bool): if True, output an identical source, except with
                source code enabled.

        Returns:
            A Source() object identical to self.
        """
        new_source = DebLine(self.deb_line)
        new_source = self._copy(new_source, source_code=source_code)
        return new_source
    
    def save_to_disk(self, save=True):
        """
        Saves the repo to disk
        """
        if save:
            super().save_to_disk()

    def _parse_debline(self, line):
        self.init_values()

        # Enabled vs. Disabled
        self.enabled = True
        if line.startswith('#'):
            self.enabled = False
            line = line.replace('#', '', 1)
            line = line.strip()

        # URI parsing
        for uri in self.uri_re.finditer(line):
            self.uris = [uri[0]]
            line_uri = line.replace(uri[0], '')

        # Options parsing
        try:
            options = self.options_re.search(line_uri).group()
            opts = self._set_options(options.strip())
            self.options = opts.copy()
            line_uri = line_uri.replace(options, '')
        except AttributeError:
            pass

        deb_list = line_uri.split()

        # Type Parsing
        self.types = [util.AptSourceType.BINARY]
        if deb_list[0] == 'deb-src':
            self.types = [util.AptSourceType.SOURCE]

        # Suite Parsing
        self.suites = [deb_list[1]]

        # Components parsing
        comps = []
        for item in deb_list[2:]:
            if not item.startswith('#'):
                comps.append(item)
            else:
                break
        self.components = comps

    def _validate(self, valid):
        """
        Ensure we have a valid debian repository line.
        """
        if valid.startswith('#'):
            self.enabled = False
            valid = valid.replace('#', '')
        valid = valid.strip()
        if not valid.startswith('deb'):
            raise util.RepoError(
                'The line %s does not appear to be a valid repo' % self.deb_line
            )

    def _set_type(self, deb_type):
        """
        Set the type of repository (deb or deb-src)
        """
        self.types = [util.AptSourceType(deb_type)]

    def _set_options(self, options):
        """
        Set the options.
        """
        # Split the option string into a list of chars, so that we can replace
        # the first and last characters ([ and ]) with spaces.
        ops = list(options)
        ops[0] = " "
        ops[-1] = " "
        options = "".join(ops).strip()

        for replacement in self.options_d:
            options = options.replace(replacement, self.options_d[replacement])

        options = options.replace('=', ',')
        options_list = options.split()

        options_output = {}

        for i in options_list:
            option = i.split(',')
            values_list = []
            for value in option[1:]:
                values_list.append(value)
            options_output[option[0]] = ' '.join(values_list)
        return options_output
