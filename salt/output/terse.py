# -*- coding: utf-8 -*-
'''

Display the terse output to user
The terse output just include XXX service is success or XXX process is dead.

'''

# Import Python libs
from __future__ import absolute_import
import logging

# Import salt libs

logging = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'terse'


def __virtual__():
    '''
    Rename to json
    '''
    return __virtualname__

def output(data):

    return "liuyang test"