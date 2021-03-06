# -*- coding: utf-8 -*-

""" Runs `all_tests.py` whenever a git pull is performed,
      and sends email of results.
    Called by `path/to/reserves/.git/hooks/post-merge` which contains the lines...
      #!/bin/bash
      source path/to/env/bin/activate
      path/to/env/python path/to/run_tests.py (this file)
    Note: run_tests.py must be executable. """

import json, os, pprint, smtplib
from email.Header import Header
from email.mime.text import MIMEText
#
import envoy


def run_main():
    """ Calls tests, sends email. """
    ( ALL_TESTS_PATH, UTF8_RAW_TO, UTF8_RAW_FROM, SMTP_PORT_RAW ) = grab_settings()
    command = u'python %s' % ALL_TESTS_PATH
    r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
    info = {
        u'std_out': r.std_out.decode(u'utf-8'), u'std_err': r.std_err.decode(u'utf-8'),
        u'status_code': r.status_code, u'command': r.command, u'history': r.history }
    parsed_info_dict = parse_info( info )
    mailer = Mailer( UTF8_RAW_TO, UTF8_RAW_FROM, SMTP_PORT_RAW, parsed_info_dict )
    mailer.send_email()
    return


def grab_settings():
    """ Grabs environmental variables.
        Called by run_main(). """
    ALL_TESTS_PATH = unicode( os.environ[u'OCRA_TESTS__ALL_TESTS_PATH'] )
    UTF8_RAW_TO = os.environ[u'OCRA_TESTS__MAIL_TO']  # json string of list of email addresses
    UTF8_RAW_FROM = os.environ[u'OCRA_TESTS__MAIL_FROM']
    SMTP_PORT_RAW = os.environ[u'OCRA_TESTS__SMTP_PORT_RAW']  # json string of dict; format like '{"smtp_port": 1025}' (or '{"smtp_port": null}'
    return ( ALL_TESTS_PATH, UTF8_RAW_TO, UTF8_RAW_FROM, SMTP_PORT_RAW )


def parse_info( info ):
    """ Checks test output; returns info-dict.
        Called by run_main(). """
    worthy_text = info[u'std_err']
    return_dict = { u'message': u'tests output...\n\n%s' % worthy_text }
    segment_start = worthy_text.find( u'Ran ' )
    worthy_slice = worthy_text[segment_start:]
    worthy_slice_cleaned = worthy_slice.strip()
    worthy_slice_words = worthy_slice_cleaned.split()
    if worthy_slice_words[-1] == u'OK':
        return_dict[u'subject'] = u'ocra interface-tests passed'
    else:
        return_dict[u'subject'] = u'ocra interface-tests PROBLEM'
    return return_dict


class Mailer( object ):
    """ Specs email handling.
        Analyzes test results (well, it will) to set subject. """

    def __init__( self, UTF8_RAW_TO, UTF8_RAW_FROM, SMTP_PORT_RAW, info_dict ):
        self.UTF8_RAW_TO = UTF8_RAW_TO
        self.UTF8_RAW_FROM = UTF8_RAW_FROM
        self.SMTP_PORT_RAW = SMTP_PORT_RAW
        self.info_dict = info_dict

    def send_email( self ):
        """ Sends email. """
        TO = self._build_mail_to()  # utf-8
        FROM = self.UTF8_RAW_FROM  # utf-8
        SUBJECT = self.info_dict[u'subject']  # unicode
        MESSAGE = self.info_dict[u'message'].encode( u'utf-8', u'replace' )
        payload = self._assemble_payload( TO, FROM, SUBJECT, MESSAGE )
        s = smtplib.SMTP( 'localhost', json.loads(self.SMTP_PORT_RAW)['smtp_port'] )
        s.sendmail( FROM, TO, payload.as_string() )
        s.quit()
        return

    def _build_mail_to( self ):
        """ Builds and returns 'to' list of email addresses.
            Called by send_email() """
        to_emails = json.loads( self.UTF8_RAW_TO )
        utf8_to_list = []
        for address in to_emails:
            utf8_to_list.append( address.encode('utf-8') )
        return utf8_to_list

    def _assemble_payload( self, TO, FROM, SUBJECT, MESSAGE ):
        """ Puts together and returns email payload.
            Called by send_email(). """
        payload = MIMEText( MESSAGE )
        payload['To'] = ', '.join( TO )
        payload['From'] = FROM
        payload['Subject'] = Header( SUBJECT, 'utf-8' )  # SUBJECT must be unicode
        return payload

    # end class Mailer




if __name__ == "__main__":
    run_main()
