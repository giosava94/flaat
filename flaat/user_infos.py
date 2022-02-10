from json import JSONEncoder
import logging
from typing import Optional

from flaat.access_tokens import AccessTokenInfo

logger = logging.getLogger(__name__)


class UserInfos:
    """Infos represents infos about an access token and the user it belongs to"""

    user_info: dict
    access_token_info: Optional[AccessTokenInfo]
    introspection_info: Optional[dict]
    valid_for_secs: int = -1

    def __init__(
        self,
        access_token_info: Optional[AccessTokenInfo],
        user_info: dict,
        introspection_info: Optional[dict],
    ):
        self.access_token_info = access_token_info
        if self.access_token_info is not None:
            self.valid_for_secs = self.access_token_info.timeleft

        self.user_info = user_info
        self.introspection_info = introspection_info

        # trigger possible post processing here
        self.post_process_dictionaries()

    def _strip_duplicate_infos(self):
        """ strip duplicate infos from the introspection_info and access_token_info.body """
        if self.introspection_info is not None:
            for key in self.user_info.keys():
                if key in self.introspection_info:
                    del self.introspection_info[key]
        if self.access_token_info is not None:
            for key in self.user_info.keys():
                if key in self.access_token_info.body:
                    del self.access_token_info.body[key]

    def post_process_dictionaries(self):
        """post_process_dictionaries can be used to do post processing on the raw dictionaries after initialization.
        Extend this class and overwrite this method to do custom post processing.
        Make sure to call super().post_process_dictionaries(), so the post processing done here is picked up.
        """
        # copy a possible 'iss' fields into the user info if it does not exist
        # This is useful if someone extracts only the user_info dictionary from us
        if "iss" not in self.user_info and self.has_key("iss"):
            self.user_info["iss"] = self["iss"]

        # striping duplicates is somewhat opinionated and is therefore not included here
        # self._strip_duplicate_infos()


    @property
    def issuer(self) -> str:
        return self.get("iss", "")

    @property
    def subject(self) -> str:
        return self.get("sub", "")

    # make the UserInfos act like a dictionary with regard to claims
    def __getitem__(self, key):
        if key in self.user_info:
            return self.user_info[key]
        if self.introspection_info is not None and key in self.introspection_info:
            return self.introspection_info[key]
        if self.access_token_info is not None and key in self.access_token_info.body:
            return self.access_token_info.body[key]
        raise KeyError(
            "Claim does not exist in user_info, access_token_info.body and introspection_info"
        )

    def __setitem__(self, key, val):
        self.user_info[key] = val

    def has_key(self, key):
        return (
            key in self.user_info
            or (
                self.access_token_info is not None
                and key in self.access_token_info.body
            )
            or (self.introspection_info is not None and key in self.introspection_info)
        )

    def get(self, key, default=None):
        if self.has_key(key):
            return self[key]
        return default

    def __str__(self):
        return f"{self.subject}@{self.issuer}"

    def toJSON(self) -> str:
        class ATEncoder(JSONEncoder):
            def default(self, o):
                return o.__dict__

        return ATEncoder(indent=4, sort_keys=True, separators=(",", ":")).encode(self)
