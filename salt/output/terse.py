# -*- coding: utf-8 -*-
'''
Display the terse output to user
The terse output just include some summary.
'''

# Import python libs
from __future__ import absolute_import
import pprint
import textwrap

# Import salt libs
import salt.utils
import salt.output
from salt.utils.locales import sdecode

# Import 3rd-party libs
import salt.ext.six as six

import logging

log = logging.getLogger(__name__)


def output(data):
    '''
    The terse Outputter is only meant to be used with the state.sls
    function, or a function that returns state return data.
    '''
    # If additional information is passed through via the "data" dictionary to
    # the highstate outputter, such as "outputter" or "retcode", discard it.
    if 'data' in data:
        data = data.pop('data')

    for host, hostdata in six.iteritems(data):
        return _format_host(host, hostdata)[0]


def _format_host(host, data):
    host = sdecode(host)

    colors = salt.utils.get_colors(
            __opts__.get('color'),
            __opts__.get('color_theme'))
    rcounts = {}
    rdurations = []
    hcolor = colors['GREEN']
    hstrs = []
    nchanges = 0

    if isinstance(data, int) or isinstance(data, str):
        # Data in this format is from saltmod.function,
        # so it is always a 'change'
        nchanges = 1
        hstrs.append((u'{0}    {1}{2[ENDC]}'
                      .format(hcolor, data, colors)))
        hcolor = colors['CYAN']  # Print the minion name in cyan
    if isinstance(data, list):
        # Errors have been detected, list them in RED!
        hcolor = colors['LIGHT_RED']
        hstrs.append((u'    {0}Data failed to compile:{1[ENDC]}'
                      .format(hcolor, colors)))
        for err in data:
            hstrs.append((u'{0}----------\n    {1}{2[ENDC]}'
                          .format(hcolor, err, colors)))
    if isinstance(data, dict):
        # Verify that the needed data is present
        data_tmp = {}
        for tname, info in six.iteritems(data):
            if isinstance(info, dict) and '__run_num__' not in info:
                err = (u'The State execution failed to record the order '
                       'in which all states were executed. The state '
                       'return missing data is:')
                hstrs.insert(0, pprint.pformat(info))
                hstrs.insert(0, err)
            if isinstance(info, dict) and 'result' in info:
                data_tmp[tname] = info
        data = data_tmp
        # Everything rendered as it should display the output
        for tname in sorted(
                data,
                key=lambda k: data[k].get('__run_num__', 0)):
            ret = data[tname]
            # Increment result counts
            rcounts.setdefault(ret['result'], 0)
            rcounts[ret['result']] += 1
            rduration = ret.get('duration', 0)
            try:
                float(rduration)
                rdurations.append(rduration)
            except ValueError:
                rduration, _, _ = rduration.partition(' ms')
                try:
                    float(rduration)
                    rdurations.append(rduration)
                except ValueError:
                    log.error('Cannot parse a float from duration {0}'
                              .format(ret.get('duration', 0)))

            tcolor = colors['GREEN']
            schanged, ctext = _format_changes(ret['changes'])
            nchanges += 1 if schanged else 0

            if schanged:
                tcolor = colors['CYAN']
            if ret['result'] is True:
                continue;
            if ret['result'] is False:
                hcolor = colors['RED']
                tcolor = colors['RED']
            if ret['result'] is None:
                hcolor = colors['LIGHT_YELLOW']
                tcolor = colors['LIGHT_YELLOW']
            comps = [sdecode(comp) for comp in tname.split('_|-')]
            state_lines = [
                u'{tcolor}----------{colors[ENDC]}',
                u'    {tcolor}      ID: {comps[1]}{colors[ENDC]}',
                u'    {tcolor}Function: {comps[0]}.{comps[3]}{colors[ENDC]}',
                u'    {tcolor}  Result: {ret[result]!s}{colors[ENDC]}',
                u'    {tcolor} Comment: {comment}{colors[ENDC]}',
            ]
            # This isn't the prettiest way of doing this, but it's readable.
            if comps[1] != comps[2]:
                state_lines.insert(
                    3, u'    {tcolor}    Name: {comps[2]}{colors[ENDC]}')
            # be sure that ret['comment'] is utf-8 friendly
            try:
                if not isinstance(ret['comment'], six.text_type):
                    ret['comment'] = str(ret['comment']).decode('utf-8')
            except UnicodeDecodeError:
                # but try to continue on errors
                pass
            try:
                comment = sdecode(ret['comment'])
                comment = comment.strip().replace(
                        u'\n',
                        u'\n' + u' ' * 14)
            except AttributeError:  # Assume comment is a list
                try:
                    comment = ret['comment'].join(' ').replace(
                        u'\n',
                        u'\n' + u' ' * 13)
                except AttributeError:
                    # Comment isn't a list either, just convert to string
                    comment = str(ret['comment'])
                    comment = comment.strip().replace(
                        u'\n',
                        u'\n' + u' ' * 14)
            # If there is a data attribute, append it to the comment
            if 'data' in ret:
                if isinstance(ret['data'], list):
                    for item in ret['data']:
                        comment = '{0} {1}'.format(comment, item)
                elif isinstance(ret['data'], dict):
                    for key, value in ret['data'].items():
                        comment = '{0}\n\t\t{1}: {2}'.format(comment, key, value)
                else:
                    comment = '{0} {1}'.format(comment, ret['data'])
            for detail in ['start_time', 'duration']:
                ret.setdefault(detail, u'')
            if ret['duration'] != '':
                ret['duration'] = u'{0} ms'.format(ret['duration'])
            svars = {
                'tcolor': tcolor,
                'comps': comps,
                'ret': ret,
                'comment': sdecode(comment),
                # This nukes any trailing \n and indents the others.
                'colors': colors
            }
            hstrs.extend([sline.format(**svars) for sline in state_lines])
            changes = u'     Changes:   ' + ctext
            hstrs.append((u'{0}{1}{2[ENDC]}'
                          .format(tcolor, changes, colors)))

            if 'warnings' in ret:
                rcounts.setdefault('warnings', 0)
                rcounts['warnings'] += 1
                wrapper = textwrap.TextWrapper(
                    width=80,
                    initial_indent=u' ' * 14,
                    subsequent_indent=u' ' * 14
                )
                hstrs.append(
                    u'   {colors[LIGHT_RED]} Warnings: {0}{colors[ENDC]}'.format(
                        wrapper.fill('\n'.join(ret['warnings'])).lstrip(),
                        colors=colors
                    )
                )

        # Append result counts to end of output
        colorfmt = u'{0}{1}{2[ENDC]}'
        rlabel = {True: u'Succeeded', False: u'Failed', None: u'Not Run', 'warnings': u'Warnings'}
        count_max_len = max([len(str(x)) for x in six.itervalues(rcounts)] or [0])
        label_max_len = max([len(x) for x in six.itervalues(rlabel)] or [0])
        line_max_len = label_max_len + count_max_len + 2  # +2 for ': '
        hstrs.append(
            colorfmt.format(
                colors['CYAN'],
                u'\nSummary for {0}\n{1}'.format(host, '-' * line_max_len),
                colors
            )
        )

        def _counts(label, count):
            return u'{0}: {1:>{2}}'.format(
                label,
                count,
                line_max_len - (len(label) + 2)
            )

        # Successful states
        changestats = []
        if None in rcounts and rcounts.get(None, 0) > 0:
            # test=True states
            changestats.append(
                colorfmt.format(
                    colors['LIGHT_YELLOW'],
                    u'unchanged={0}'.format(rcounts.get(None, 0)),
                    colors
                )
            )
        if nchanges > 0:
            changestats.append(
                colorfmt.format(
                    colors['GREEN'],
                    u'changed={0}'.format(nchanges),
                    colors
                )
            )
        if changestats:
            changestats = u' ({0})'.format(', '.join(changestats))
        else:
            changestats = u''
        hstrs.append(
            colorfmt.format(
                colors['GREEN'],
                _counts(
                    rlabel[True],
                    rcounts.get(True, 0) + rcounts.get(None, 0)
                ),
                colors
            ) + changestats
        )

        # Failed states
        num_failed = rcounts.get(False, 0)
        hstrs.append(
            colorfmt.format(
                colors['RED'] if num_failed else colors['CYAN'],
                _counts(rlabel[False], num_failed),
                colors
            )
        )

        num_warnings = rcounts.get('warnings', 0)
        if num_warnings:
            hstrs.append(
                colorfmt.format(
                    colors['LIGHT_RED'],
                    _counts(rlabel['warnings'], num_warnings),
                    colors
                )
            )
        totals = u'{0}\nTotal states run: {1:>{2}}'.format('-' * line_max_len,
                                               sum(six.itervalues(rcounts)) - rcounts.get('warnings', 0),
                                               line_max_len - 7)
        hstrs.append(colorfmt.format(colors['CYAN'], totals, colors))

    hstrs.insert(0, (u'{0}{1}:{2[ENDC]}'.format(hcolor, host, colors)))
    return u'\n'.join(hstrs), nchanges > 0


def _format_changes(changes):
    '''
    Format the changes dict based on what the data is
    '''
    global __opts__  # pylint: disable=W0601

    if not changes:
        return False, u''

    if not isinstance(changes, dict):
        return True, u'Invalid Changes data: {0}'.format(changes)

    ret = changes.get('ret')
    if ret is not None and changes.get('out') == 'highstate':
        ctext = u''
        changed = False
        for host, hostdata in six.iteritems(ret):
            s, c = _format_host(host, hostdata)
            ctext += u'\n' + u'\n'.join((u' ' * 14 + l) for l in s.splitlines())
            changed = changed or c
    else:
        changed = True
        opts = __opts__.copy()
        # Pass the __opts__ dict. The loader will splat this modules __opts__ dict
        # anyway so have to restore it after the other outputter is done
        if __opts__['color']:
            __opts__['color'] = u'CYAN'
        __opts__['nested_indent'] = 14
        ctext = u'\n'
        ctext += salt.output.out_format(
                changes,
                'nested',
                __opts__)
        __opts__ = opts
    return changed, ctext


def _format_terse(tcolor, comps, ret, colors, tabular):
    '''
    Terse formatting of a message.
    '''
    result = u'Clean'
    if ret['changes']:
        result = u'Changed'
    if ret['result'] is False:
        result = u'Failed'
    elif ret['result'] is None:
        result = u'Differs'
    if tabular is True:
        fmt_string = ''
        if 'warnings' in ret:
            fmt_string += u'{c[LIGHT_RED]}Warnings:\n{w}{c[ENDC]}\n'.format(
                c=colors, w='\n'.join(ret['warnings'])
            )
        fmt_string += u'{0}'
        fmt_string += u'{2:>10}.{3:<10} {4:7}   Name: {1}{5}'
    elif isinstance(tabular, str):
        fmt_string = tabular
    else:
        fmt_string = ''
        if 'warnings' in ret:
            fmt_string += u'{c[LIGHT_RED]}Warnings:\n{w}{c[ENDC]}'.format(
                c=colors, w='\n'.join(ret['warnings'])
            )
        fmt_string += u' {0} Name: {1} - Function: {2}.{3} - Result: {4}'
        fmt_string += u'{5}'

    msg = fmt_string.format(tcolor,
                            comps[2],
                            comps[0],
                            comps[-1],
                            result,
                            colors['ENDC'],
                            ret)
    return msg
