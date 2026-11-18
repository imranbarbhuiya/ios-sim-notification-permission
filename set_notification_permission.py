#!/usr/bin/env python3
"""Sets an app's notification permission on a booted iOS simulator.

`xcrun simctl privacy` cannot change notifications ("Failed to create TCC
authorization record / Operation not permitted" on iOS 27). The simulator keeps
that permission in Library/BulletinBoard/VersionedSectionInfo.plist: one
NSKeyedArchiver-encoded BBSectionInfo per bundle id, the record SpringBoard
writes when a user answers the prompt. This script writes the same record and
restarts the services that cache it, so the app reads the new status.

    set_notification_permission.py <udid> <bundle-id> <grant|deny|reset> [--name "Display Name"]
"""

import argparse
import os
import plistlib
import subprocess
import sys
import time
from plistlib import UID

AUTHORIZATION = {"grant": 2, "deny": 1}
SERVICES = ["com.apple.SpringBoard", "com.apple.usernotificationsd"]
# Seconds between the Cocoa reference date (2001-01-01) and the Unix epoch.
COCOA_EPOCH = 978307200


def section_info(bundle_id: str, name: str, status: int) -> bytes:
    """A BBSectionInfo archive in the shape iOS 27 writes for a user's answer."""
    settings = {
        "$class": UID(4),
        "authorizationStatus": status,
        "authorizationExpirationDate": UID(0),
        "lastUserGrantedAuthorizationDate": UID(0),
        "alertType": 1,
        "pushSettings": 63 if status == 2 else 0,
        "showsInNotificationCenter": status == 2,
        "showsInLockScreen": status == 2,
        "showsOnExternalDevices": status == 2,
        "notificationCenterSetting": 2 if status == 2 else 1,
        "lockScreenSetting": 2 if status == 2 else 1,
        "remoteNotificationsSetting": 2 if status == 2 else 1,
        "carPlaySetting": 0,
        "criticalAlertSetting": 0,
        "timeSensitiveSetting": 0,
        "userConfiguredTimeSensitiveSetting": False,
        "directMessagesSettingKey": 0,
        "userConfiguredDirectMessagesSetting": False,
        "announceSetting": 1,
        "announcePriority": 0,
        "bulletinGroupingSetting": 0,
        "contentPreviewSetting": 0,
        "prioritizationSetting": 2,
        "summarizationSetting": 2,
        "scheduledDeliverySetting": 1,
        "showsCustomSettingsLink": False,
        "muteAssertion": UID(0),
    }
    info = {
        "$class": UID(10),
        "sectionID": UID(2),
        "sectionInfoSettings": UID(3),
        "lastSettingChangeDate": UID(5),
        "appName": UID(7),
        "displayName": UID(8),
        "version": UID(9),
        "lastSettingSource": 2,
        "sectionType": 0,
        "sectionCategory": 0,
        "subsectionPriority": 0,
        "suppressFromSettings": False,
        "suppressedSettings": 0,
        "isRestricted": False,
        "isModificationAllowed": False,
        "hasEverBeenUserChanged": False,
        "isAppClip": False,
        "isLocked": False,
        "hideWeeApp": False,
        "customSettingsBundle": UID(0),
        "customSettingsDetailControllerClass": UID(0),
        "icon": UID(0),
        "subsections": UID(0),
        "subsectionID": UID(0),
        "managedSectionInfoSettings": UID(0),
        "factorySectionID": UID(0),
        "dataProviderIDs": UID(0),
        "pathToWeeAppPluginBundle": UID(0),
    }
    objects = [
        "$null",
        info,
        bundle_id,
        settings,
        {"$classname": "BBSectionInfoSettings", "$classes": ["BBSectionInfoSettings", "NSObject"]},
        {"NS.time": time.time() - COCOA_EPOCH, "$class": UID(6)},
        {"$classname": "NSDate", "$classes": ["NSDate", "NSObject"]},
        name,
        name,
        0,
        {"$classname": "BBSectionInfo", "$classes": ["BBSectionInfo", "NSObject"]},
    ]
    archive = {"$version": 100000, "$archiver": "NSKeyedArchiver", "$top": {"root": UID(1)}, "$objects": objects}
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)


def simctl(*args: str) -> str:
    return subprocess.run(["xcrun", "simctl", *args], check=True, capture_output=True, text=True).stdout


def data_dir(udid: str) -> str:
    return os.path.expanduser(f"~/Library/Developer/CoreSimulator/Devices/{udid}/data")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("udid")
    parser.add_argument("bundle_id")
    parser.add_argument("action", choices=["grant", "deny", "reset"])
    parser.add_argument("--name", help="display name; defaults to the bundle id")
    args = parser.parse_args()

    path = os.path.join(data_dir(args.udid), "Library", "BulletinBoard", "VersionedSectionInfo.plist")
    # SpringBoard rewrites the file from memory as it stops, so it stops first.
    for service in SERVICES:
        simctl("spawn", args.udid, "launchctl", "stop", service)
    with open(path, "rb") as handle:
        store = plistlib.load(handle)
    sections = store.setdefault("sectionInfo", {})
    if args.action == "reset":
        sections.pop(args.bundle_id, None)
    else:
        sections[args.bundle_id] = section_info(args.bundle_id, args.name or args.bundle_id, AUTHORIZATION[args.action])
    with open(path + ".tmp", "wb") as handle:
        plistlib.dump(store, handle, fmt=plistlib.FMT_BINARY)
    os.replace(path + ".tmp", path)
    for service in SERVICES:
        simctl("spawn", args.udid, "launchctl", "start", service)
    print(f"{args.action} notifications for {args.bundle_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
