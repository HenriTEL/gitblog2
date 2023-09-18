"""
This type stub file was generated by pyright.
"""

GIT_CREDENTIAL_USERPASS_PLAINTEXT = ...
GIT_CREDENTIAL_SSH_KEY = ...
GIT_CREDENTIAL_SSH_CUSTOM = ...
GIT_CREDENTIAL_DEFAULT = ...
GIT_CREDENTIAL_SSH_INTERACTIVE = ...
GIT_CREDENTIAL_USERNAME = ...
GIT_CREDENTIAL_SSH_MEMORY = ...
class Username:
    """Username credentials

    This is an object suitable for passing to a remote's credentials
    callback and for returning from said callback.
    """
    def __init__(self, username) -> None:
        ...
    
    @property
    def credential_type(self):
        ...
    
    @property
    def credential_tuple(self): # -> tuple[Unknown]:
        ...
    
    def __call__(self, _url, _username, _allowed): # -> Self@Username:
        ...
    


class UserPass:
    """Username/Password credentials

    This is an object suitable for passing to a remote's credentials
    callback and for returning from said callback.
    """
    def __init__(self, username, password) -> None:
        ...
    
    @property
    def credential_type(self):
        ...
    
    @property
    def credential_tuple(self): # -> tuple[Unknown, Unknown]:
        ...
    
    def __call__(self, _url, _username, _allowed): # -> Self@UserPass:
        ...
    


class Keypair:
    """
    SSH key pair credentials.

    This is an object suitable for passing to a remote's credentials
    callback and for returning from said callback.

    Parameters:

    username : str
        The username being used to authenticate with the remote server.

    pubkey : str
        The path to the user's public key file.

    privkey : str
        The path to the user's private key file.

    passphrase : str
        The password used to decrypt the private key file, or empty string if
        no passphrase is required.
    """
    def __init__(self, username, pubkey, privkey, passphrase) -> None:
        ...
    
    @property
    def credential_type(self):
        ...
    
    @property
    def credential_tuple(self): # -> tuple[Unknown, Unknown, Unknown, Unknown]:
        ...
    
    def __call__(self, _url, _username, _allowed): # -> Self@Keypair:
        ...
    


class KeypairFromAgent(Keypair):
    def __init__(self, username) -> None:
        ...
    


class KeypairFromMemory(Keypair):
    @property
    def credential_type(self):
        ...
    


