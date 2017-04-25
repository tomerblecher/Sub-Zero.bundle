# coding=utf-8

import subliminal

# patch subliminal's subtitle and provider base
from .subtitle import PatchedSubtitle
from .http import RetryingSession
subliminal.subtitle.Subtitle = PatchedSubtitle

try:
    subliminal.provider_manager.register('napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider',)
except ValueError:
    # already registered
    pass

# inject our requests.Session wrapper for automatic retry
subliminal.providers.addic7ed.Session = RetryingSession
subliminal.providers.podnapisi.Session = RetryingSession
subliminal.providers.tvsubtitles.Session = RetryingSession
subliminal.providers.opensubtitles.Session = RetryingSession
subliminal.providers.legendastv.Session = RetryingSession
subliminal.providers.napiprojekt.Session = RetryingSession
subliminal.providers.shooter.Session = RetryingSession
subliminal.providers.subscenter.Session = RetryingSession

from subliminal.providers.addic7ed import Addic7edSubtitle
from subliminal.providers.podnapisi import PodnapisiSubtitle
from subliminal.providers.tvsubtitles import TVsubtitlesSubtitle
from subliminal.providers.opensubtitles import OpenSubtitlesSubtitle
from subliminal.providers.legendastv import LegendasTVSubtitle
from subliminal.providers.napiprojekt import NapiProjektSubtitle
from subliminal.providers.shooter import ShooterSubtitle
from subliminal.providers.subscenter import SubsCenterSubtitle

# add our patched base classes
setattr(Addic7edSubtitle, "__bases__", (PatchedSubtitle,))
setattr(PodnapisiSubtitle, "__bases__", (PatchedSubtitle,))
setattr(TVsubtitlesSubtitle, "__bases__", (PatchedSubtitle,))
setattr(OpenSubtitlesSubtitle, "__bases__", (PatchedSubtitle,))
setattr(LegendasTVSubtitle, "__bases__", (PatchedSubtitle,))
setattr(NapiProjektSubtitle, "__bases__", (PatchedSubtitle,))
setattr(ShooterSubtitle, "__bases__", (PatchedSubtitle,))
setattr(SubsCenterSubtitle, "__bases__", (PatchedSubtitle,))

from .core import scan_video, search_external_subtitles, list_all_subtitles, save_subtitles, refine
from .score import compute_score
from .extensions import provider_manager

# patch subliminal's core functions
subliminal.scan_video = subliminal.core.scan_video = scan_video
subliminal.core.search_external_subtitles = search_external_subtitles
subliminal.save_subtitles = subliminal.core.save_subtitles = save_subtitles
subliminal.refine = subliminal.core.refine = refine

# add our own list_all_subtitles
subliminal.list_all_subtitles = subliminal.core.list_all_subtitles = list_all_subtitles
subliminal.provider_manager = subliminal.core.provider_manager = provider_manager
