# coding=utf-8
import logging
import logger

from item_details import ItemDetailsMenu
from refresh_item import RefreshItem
from menu_helpers import add_ignore_options, dig_tree, set_refresh_menu_state, \
    should_display_ignore, enable_channel_wrapper, default_thumb, debounce, ObjectContainer, SubFolderObjectContainer
from main import fatality, IgnoreMenu
from advanced import DispatchRestart
from subzero.constants import ART, PREFIX, DEPENDENCY_MODULE_NAMES
from support.scheduler import scheduler
from support.config import config
from support.helpers import timestamp, df
from support.ignore import ignore_list
from support.items import get_all_items, get_items_info, \
    get_item_kind_from_rating_key

# init GUI
ObjectContainer.art = R(ART)
ObjectContainer.no_cache = True

# default thumb for DirectoryObjects
DirectoryObject.thumb = default_thumb

# noinspection PyUnboundLocalVariable
route = enable_channel_wrapper(route)
# noinspection PyUnboundLocalVariable
handler = enable_channel_wrapper(handler)


@route(PREFIX + '/section/firstLetter/key', deeper=bool)
def FirstLetterMetadataMenu(rating_key, key, title=None, base_title=None, display_items=False, previous_item_type=None,
                            previous_rating_key=None):
    """
    displays the contents of a section filtered by the first letter
    :param rating_key: actually is the section's key
    :param key: the firstLetter wanted
    :param title: the first letter, or #
    :param deeper:
    :return:
    """
    title = base_title + " > " + unicode(title)
    oc = SubFolderObjectContainer(title2=title, no_cache=True, no_history=True)

    items = get_all_items(key="first_character", value=[rating_key, key], base="library/sections", flat=False)
    kind, deeper = get_items_info(items)
    dig_tree(oc, items, MetadataMenu,
             pass_kwargs={"base_title": title, "display_items": deeper, "previous_item_type": kind,
                          "previous_rating_key": rating_key})
    return oc


@route(PREFIX + '/section/contents', display_items=bool)
def MetadataMenu(rating_key, title=None, base_title=None, display_items=False, previous_item_type=None,
                 previous_rating_key=None):
    """
    displays the contents of a section based on whether it has a deeper tree or not (movies->movie (item) list; series->series list)
    :param rating_key:
    :param title:
    :param base_title:
    :param display_items:
    :param previous_item_type:
    :param previous_rating_key:
    :return:
    """
    title = unicode(title)
    item_title = title
    title = base_title + " > " + title
    oc = SubFolderObjectContainer(title2=title, no_cache=True, no_history=True)

    current_kind = get_item_kind_from_rating_key(rating_key)

    if display_items:
        items = get_all_items(key="children", value=rating_key, base="library/metadata")
        kind, deeper = get_items_info(items)
        dig_tree(oc, items, MetadataMenu,
                 pass_kwargs={"base_title": title, "display_items": deeper, "previous_item_type": kind,
                              "previous_rating_key": rating_key})
        # we don't know exactly where we are here, only add ignore option to series
        if should_display_ignore(items, previous=previous_item_type):
            add_ignore_options(oc, "series", title=item_title, rating_key=rating_key, callback_menu=IgnoreMenu)

        timeout = 30
        if current_kind == "season":
            timeout = 360
        elif current_kind == "series":
            timeout = 1800

        # add refresh
        oc.add(DirectoryObject(
            key=Callback(RefreshItem, rating_key=rating_key, item_title=title, refresh_kind=current_kind,
                         previous_rating_key=previous_rating_key, timeout=timeout * 1000, randomize=timestamp()),
            title=u"Refresh: %s" % item_title,
            summary="Refreshes the %s, possibly searching for missing and picking up new subtitles on disk" % current_kind
        ))
        oc.add(DirectoryObject(
            key=Callback(RefreshItem, rating_key=rating_key, item_title=title, force=True,
                         refresh_kind=current_kind, previous_rating_key=previous_rating_key, timeout=timeout * 1000,
                         randomize=timestamp()),
            title=u"Auto-Find subtitles: %s" % item_title,
            summary="Issues a forced refresh, ignoring known subtitles and searching for new ones"
        ))
    else:
        return ItemDetailsMenu(rating_key=rating_key, title=title, item_title=item_title)

    return oc


@route(PREFIX + '/ignore_list')
def IgnoreListMenu():
    oc = SubFolderObjectContainer(title2="Ignore list", replace_parent=True)
    for key in ignore_list.key_order:
        values = ignore_list[key]
        for value in values:
            add_ignore_options(oc, key, title=ignore_list.get_title(key, value), rating_key=value,
                               callback_menu=IgnoreMenu)
    return oc


@route(PREFIX + '/history')
def HistoryMenu():
    from support.history import get_history
    history = get_history()
    oc = SubFolderObjectContainer(title2="History", replace_parent=True)

    for item in history.history_items:
        oc.add(DirectoryObject(
            key=Callback(ItemDetailsMenu, title=item.title, item_title=item.item_title,
                         rating_key=item.rating_key),
            title=u"%s (%s)" % (item.item_title, item.mode_verbose),
            summary=u"%s in %s (%s, score: %s), %s" % (item.lang_name, item.section_title,
                                                       item.provider_name, item.score, df(item.time))
        ))

    return oc


@route(PREFIX + '/missing/refresh')
@debounce
def RefreshMissing(randomize=None):
    scheduler.dispatch_task("SearchAllRecentlyAddedMissing")
    header = "Refresh of recently added items with missing subtitles triggered"
    return fatality(header=header, replace_parent=True)


@route(PREFIX + '/ValidatePrefs', enforce_route=True)
def ValidatePrefs():
    Core.log.setLevel(logging.DEBUG)
    Log.Debug("Validate Prefs called.")

    # SZ config debug
    Log.Debug("--- SZ Config-Debug ---")
    for attr in [
            "app_support_path", "data_path", "data_items_path", "plugin_log_path", "server_log_path", "enable_agent",
            "enable_channel", "permissions_ok", "missing_permissions", "fs_encoding"]:
        Log.Debug("config.%s: %s", attr, getattr(config, attr))
    Log.Debug("Platform: %s", Core.runtime.platform)
    Log.Debug("OS: %s", Core.runtime.os)
    Log.Debug("-----------------------")

    # cache the channel state
    update_dict = False
    restart = False

    # reset pin
    Dict["pin_correct_time"] = None

    config.initialize()
    if "channel_enabled" not in Dict:
        update_dict = True

    elif Dict["channel_enabled"] != config.enable_channel:
        Log.Debug("Channel features %s, restarting plugin", "enabled" if config.enable_channel else "disabled")
        update_dict = True
        restart = True

    if update_dict:
        Dict["channel_enabled"] = config.enable_channel
        Dict.Save()

    if restart:
        DispatchRestart()

    scheduler.setup_tasks()
    set_refresh_menu_state(None)

    if Prefs["log_console"]:
        Core.log.addHandler(logger.console_handler)
        Log.Debug("Logging to console from now on")
    else:
        Core.log.removeHandler(logger.console_handler)
        Log.Debug("Stop logging to console")

    Log.Debug("Setting log-level to %s", Prefs["log_level"])
    logger.register_logging_handler(DEPENDENCY_MODULE_NAMES, level=Prefs["log_level"])
    Core.log.setLevel(logging.getLevelName(Prefs["log_level"]))

    return
