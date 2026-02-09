# Anti-bot headers and rotation strategies
import random
from typing import Dict, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class BrowserProfile:
    user_agent: str
    accept_language: str
    accept_encoding: str
    platform: str

class HeaderManager:     #Manage and rotate HTTP headers to avoid detection
    
    def __init__(self):
        self._profiles = self._load_browser_profiles()
        self._current_profile_index = 0
        
    def _load_browser_profiles(self) -> List[BrowserProfile]:   #Load realistic browser profiles
        return [
            BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                platform="Win32"
            ),
            BrowserProfile(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                accept_language="en-GB,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                platform="MacIntel"
            ),
            BrowserProfile(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                accept_language="en-US,en;q=0.8",
                accept_encoding="gzip, deflate",
                platform="Linux x86_64"
            )
        ]
    
    def get_headers(self) -> Dict[str, str]:       # Get rotated headers for request.
        profile = self._profiles[self._current_profile_index]
        self._current_profile_index = (self._current_profile_index + 1) % len(self._profiles)
        
        headers = {
            "User-Agent": profile.user_agent,
            "Accept-Language": profile.accept_language,
            "Accept-Encoding": profile.accept_encoding,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        logger.debug("Generated headers", profile_index=self._current_profile_index)
        return headers
    
    def rotate_user_agent(self):    #Manually rotate user agent.
        self._current_profile_index = random.randint(0, len(self._profiles) - 1)