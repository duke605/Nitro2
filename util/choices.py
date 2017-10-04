from argparse import ArgumentTypeError
import re

def user(server):

    def test(s):
        match = re.search('^<@!?(\d+?)>$', s) or re.search('^(\d+)$', s)

        # Checking if string was mention
        if not match:
            raise ArgumentTypeError(f'invalid value: {s} (must be mention or user\'s id)')

        u = server.get_member(match.group(1))

        # Checking if user found
        if not u:
            raise ArgumentTypeError(f'invalid user id: {match.group(1)} (user could not be found)')

        return u

    return test

def nt_user(server):

    def test(s):
        match = re.search('^<@!?(\d+?)>$', s) or re.search('^(\d+)$', s)

        if not match:
            return s

        u = server.get_member(match.group(1))

        # Checking if user found
        if not u:
            raise ArgumentTypeError(f'invalid user id: {match.group(1)} (user could not be found)')

        return u

    return test
