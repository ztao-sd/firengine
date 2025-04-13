from getpass import getpass

import keyring


def get_user_password_keyring(namespace: str, prompt: bool = True) -> (str | None, str | None):
    user, passwd = None, None
    if cred := keyring.get_credential(namespace, None):
        user, passwd = cred.username, cred.password
    else:
        if prompt:
            user = input("Username: ")
            passwd = getpass()
            keyring.set_password(namespace, user, passwd)

    return user, passwd
