# -*- coding: utf-8 -*-
'''

Display the terse output to user
The terse output just include XXX service is success or XXX process is dead.

'''

# Import Python libs
from __future__ import absolute_import
import logging
from string import Template

# Import salt libs
from salt.utils import get_colors
import salt.utils.locales

log = logging.getLogger(__name__)


def __virtual__():
    return "terse"


class TerseDisplay(object):
    '''
    manage the terse ouput
    '''

    def __init__(self):
        self.__dict__.update(
            get_colors(
                __opts__.get('color'),
                __opts__.get('color_theme')
            )
        )
        self.strip_colors = __opts__.get('strip_colors', True)

    def ustring(self,
                indent,
                color,
                msg,
                prefix='',
                suffix='',
                endc=None):

        if endc is None:
            endc = self.ENDC

        indent *= ' '
        fmt = u'{0}{1}{2}{3}{4}{5}'

        try:
            return fmt.format(indent, color, prefix, msg, endc, suffix)
        except UnicodeDecodeError:
            return fmt.format(indent, color, prefix, salt.utils.locales.sdecode(msg), endc, suffix)

    def display(self, ret, indent, prefix, flag):

        if flag is True:
            # the result is True use green display
            return self.ustring(
                indent,
                self.GREEN,
                ret,
                prefix=prefix
            )

        elif flag is False:
            # the result is false use red display
            return self.ustring(
                indent,
                self.RED,
                ret,
                prefix=prefix
            )


def output(data):
    '''
        display the terse output data
    '''
    # structure the output data
    terse = TerseDisplay()
    retData = []
    itemTemplate = Template('$minion \n$separator \n$itemRet')
    for minion_id, data_minion in data.items():
        # use the result to change the output color
        itemRetList = ['%s' % (terse.display(value['comment'], __opts__.get('output_indent', 0), '', value['result']))
                       for key, value in data[minion_id].items()]
        retData.append(itemTemplate.safe_substitute(minion = minion_id, separator = '=' * len(minion_id), itemRet = '\n'.join(itemRetList)))

    return '\n'.join(retData)
