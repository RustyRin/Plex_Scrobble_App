import logging

from flask import Flask, request
import json
import os
import time
import requests
import pylast


app = Flask(__name__)

"""
Structure of a BASIC PSA_JSON
{
    "status":       "", # playing, scrobbled, stopped
    "listned_at":   0,  # UNIX timestamp of when the track was play(ed)
    "artist":       "", # artist of the song
    "album_artist": "", # artist owner of the album
    "album":        "", # name of the album
    "track_title":  "", # title of the song
    "track_number": 0,  # track number in the album
    "track_mbid":   ""  # MusicBrainz ID for the TRACK.
}

Structure of a ADVANCED PSA_JSON
(This is a work in progress and subject to change)
{
    "status":           "",     # playing, scrobbled, stopped
    "listned_at":       0,      # UNIX timestamp of when the track was play(ed)
    "artist":           "",     # artist of the song
    "artist_mbids":     [""],   # MusicBrainz IDs of the artists. List of all artist IDS
    "album":            "",     # name of the album
    "album_mbid:        "",     # MusicBrainz ID of the release (album)
    "track_title":      "",     # Title of the song
    "track_number":     0,      # track number in the album
    "track_mbid":       "",     # MusicBrainz ID for the TRACK
    "recording_mbid":   "",     # MusicBrainz ID of the recording
    "track_duration":   0       # Duration of the song in ms
}
"""


def make_payload_lb(scrobble: dict, now_playing: bool) -> list:
    """
    Makes the main JSON payload for ListenBrainz
    :param scrobble: Standard PSA_JSON
    :param now_playing: True for currently playing
    :return: dict of the paylaod
    """
    # Might not need
    payload = []
    s_payload = {}

    # Time
    try:
        if not now_playing:
            s_payload["listened_at"] = int(time.time())
    except:
        # Time is broken
        pass

    # Initialize Constants
    try:
        s_payload["track_metadata"] = {}
        s_payload["track_metadata"]["additional_info"] = {}
        s_payload["track_metadata"]["additional_info"]["media_player"].append("Plex")
        s_payload["track_metadata"]["additional_info"]["submission_client"].append("Plex_Scrobble_App")
    except:
        pass

    # Basic Information
    # Artist
    try:
        s_payload["track_metadata"]["artist_name"] = scrobble["artist"]
    except Exception as e:
        logging.info("Looks like artist_name was not set by parse_plex...")
        logging.error(e)

    # Album
    try:
        s_payload["track_metadata"]["album_name"] = scrobble["album"]
    except Exception as e:
        logging.info("Looks like album_name was not set by parse_plex...")
        logging.error(e)

    # Track Title
    try:
        s_payload["track_metadata"]["track_name"] = scrobble["track_title"]
    except Exception as e:
        logging.info("Looks like track_title was not set by parse_plex...")
        logging.error(e)

    # Track Number
    try:
        s_payload["track_metadata"]["additional_info"]["tracknumber"] = scrobble["track_number"]
    except Exception as e:
        logging.info("Looks like track_number was not set by parse_plex...")
        logging.error(e)

    # Track MBID
    try:
        s_payload["track_metadata"]["additional_info"]["track_mbid"] = scrobble["track_mbid"]
    except Exception as e:
        logging.info("Looks like track_mbid was not set or not found by parse_plex...")
        logging.error(e)

    # Advanced features
    if advanced:

        # Artist MBID
        # I know LB takes in a list, but the plexapi just gives one.
        try:
            s_payload["track_metadata"]["additional_info"]["artist_mbids"] = [scrobble["artist_mbid"]]
        except KeyError:
            pass

        # Album MBID
        try:
            s_payload["track_metadata"]["additional_info"]["release_mbid"] = scrobble["album_mbid"]
        except KeyError:
            pass

        # Duration ms
        try:
            s_payload["track_metadata"]["additional_info"]["duration_ms"] = scrobble["track_duration"]
        except KeyError:
            pass

    payload.append(s_payload)
    return payload


def submit_lb(scrobble: dict):

    # Get listen_type
    if scrobble["status"] == "playing":
        # Currently playing
        listen_type = "playing_now"

        # Make payload
        payload = make_payload_lb(scrobble=scrobble, now_playing=True)

    else:
        # Scrobbled
        listen_type = "single"

        # Make Payload
        payload = make_payload_lb(scrobble=scrobble, now_playing=False)

    lb_json = {
            "listen_type": listen_type,
            "payload": payload
        }

    response = requests.post(
        url="https://api.listenbrainz.org/1/submit-listens",
        json=lb_json,
        headers={
            "Authorization": "Token " + os.environ["LB_API_TOKEN"]
        }
    )
    if response.status_code != 200:
        logging.info("This is the ListenBrainz error response:")
        logging.error(response.content)


def get_logging():
    """
    Uses ENV to set logging levels. Defaults to ERROR
    """
    match os.environ["LOGGING"]:
        case "DEBUG":
            logging.basicConfig(level=logging.DEBUG)
        case "INFO":
            logging.basicConfig(level=logging.INFO)
        case "WARNING":
            logging.basicConfig(level=logging.WARNING)
        case "ERROR":
            logging.basicConfig(level=logging.ERROR)
        case "CRITICAL":
            logging.basicConfig(level=logging.CRITICAL)
        case _:
            # Default
            logging.basicConfig(level=logging.ERROR)


def parse_plex(webhook_json) -> dict | None:
    """
    This parses the utter insanity that is a Plex webhook
    :param webhook_json: The raw Plex Webhook JSON
    :return: A JSON in the format of the PSA default JSON
    """

    # Is event music and the desired user
    if (webhook_json["Account"]["title"] == os.environ["PLEX_USERNAME"]) and \
            (webhook_json["Metadata"]["type"] == "track"):
        scrobble = {}
    else:
        return

    # Get Event Type (Play, Scrobble, Pause)
    match webhook_json["event"]:

        # Playing
        case "media.play":
            scrobble["status"] = "playing"
        case "media.resume":
            scrobble["status"] = "playing"

        # Played
        case "media.scrobble":
            scrobble["status"] = "scrobbled"

        # Paused
        case "media.pause":
            logging.info("ListenBrainz and LastFM do not support ending \"Now Playing\"")
            NotImplementedError("ListenBrainz and LastFM do not support ending \"Now Playing\"")

        case _:
            logging.info("Used default case for status...")
            NotImplementedError("ListenBrainz and LastFM do not support ending \"Now Playing\"")

    # Get Artist
    try:
        # If the artist of a song =! the album artist, track has a originalTitle
        # tag. This tag does not appear when it does match.
        scrobble.update({"artist": webhook_json["Metadata"]["originalTitle"]})
    except KeyError:
        scrobble.update({"artist": webhook_json["Metadata"]["grandparentTitle"]})
    except Exception as e:
        # Missing
        logging.info("Failed getting track artist...")
        logging.error(e)

    # Get Album Artist
    try:
        scrobble.update({"album_artist": webhook_json["Metadata"]["grandparentTitle"]})
    except Exception as e:
        # Missing
        logging.info("Failed getting album artst...")
        logging.error(e)

    # Get Album
    try:
        scrobble.update({"album": webhook_json["Metadata"]["parentTitle"]})
    except Exception as e:
        # Missing
        logging.info("Failed getting album...")
        logging.error(e)

    # Get Track Title
    try:
        scrobble.update({"track_title": webhook_json["Metadata"]["title"]})
    except Exception as e:
        # Missing
        logging.info("Failed getting track title...")
        logging.error(e)

    # Get Track number
    try:
        scrobble.update({"track_number": webhook_json["Metadata"]["index"]})
    except Exception as e:
        # Missing
        logging.info("Failed getting the track number...")
        logging.error(e)

    # Get Track MBID
    try:
        # The first 7 characters are `mbid://` that we don't need
        scrobble.update({"track_mbid": webhook_json["Metadata"]["Guid"][0]["id"][7:]})
    except Exception as e:
        # Missing
        logging.info("Failed to get the track MBID...")
        logging.error(e)

    # Doing Advanced features now
    if advanced:

        # Getting song
        song_guid = webhook_json["Metadata"]["guid"]
        ekey = webhook_json["Metadata"]["key"]
        song = plex.fetchItem(ekey=ekey, guid__exact=song_guid)

        # Get Artist MBIDs
        try:
            scrobble.update({"artist_mbid": str(song.artist().guids[0].id[7:])})
        except Exception as e:
            logging.info("Failed to get the artist MBID")
            logging.info(e)

        # Get Album MBID
        try:
            scrobble.update({"album_mbid": str(song.album().guids[0].id[7:])})
        except Exception as e:
            logging.info("Failed to get the album MBID")
            logging.info(e)

        # Get recording MBID
        # Skipping for now

        # Get track duration
        try:
            scrobble.update({"track_duration": song.duration})
        except Exception as e:
            logging.info("Failed to get the duration")
            logging.info(e)

    return scrobble


def sign_in_lastfm() -> pylast.LastFMNetwork:
    """
    Does everything to sign into LastFM
    :return: pylast.LastFMNetwork
    """

    network = pylast.LastFMNetwork(
        api_key=os.environ["LFM_API_KEY"],
        api_secret=os.environ["LFM_API_SECRET"],
        username=os.environ["LFM_USERNAME"],
        password_hash=pylast.md5(os.environ["LFM_PASSWORD"])
    )

    return network


def submit_lfm(network: pylast.LastFMNetwork, scrobble: dict):
    """
    Posts the given scrobble to LastFM
    :param network: pylast network object
    :param scrobble: Standard PSA scrobble JSON
    :return: null
    """

    #logging.info(int((scrobble["track_duration"])/1000))
    if scrobble["status"] == "playing":
        network.update_now_playing(
            artist=scrobble["artist"],
            title=scrobble["track_title"],
            album=scrobble["album"],
            #duration=int((scrobble["duration"])/1000),
            track_number=scrobble["track_number"],
            mbid=scrobble["track_mbid"]
        )
    elif scrobble["status"] == "scrobbled":
        network.scrobble(
            artist=scrobble["artist"],
            title=scrobble["track_title"],
            album=scrobble["album"],
            #duration=int((scrobble["duration"]) / 1000),
            track_number=scrobble["track_number"],
            mbid=scrobble["track_mbid"],
            timestamp=int(time.time())
        )


# Set Logging level
get_logging()

# Check if they set a Plex User
if "PLEX_USERNAME" not in os.environ:
    logging.error("You do not seem to have set your `PLEX_USERNAME` into the environment variables. Please set it")
    LookupError

# Logging into LastFM
#try:
network = sign_in_lastfm()
#except Exception as e:
    #logging.error("Failed to sign into LastFM! If you were planning on using LastFM, please review your credentials.")
    #logging.error(e)


# Checking if advanced is on
# If it is, login to Plex
advanced = False
if "ADVANCED" in os.environ:
    if os.environ["ADVANCED"].lower() == "true":
        advanced = True
        logging.info("Advanced mode on!")

if advanced:
    # Advanced on

    # Checking if they set a login method
    if "LOGIN_METHOD" in os.environ:
        # They set a login method
        match os.environ["LOGIN_METHOD"]:
            case "USER_PASS_SERVER":
                from plexapi.myplex import MyPlexAccount

                plex_account = MyPlexAccount(os.environ["PLEX_USERNAME"], os.environ["PLEX_PASSWORD"])
                plex = plex_account.resource(os.environ["SERVER_NAME"]).connect()
            case "URL_TOKEN":
                from plexapi.server import PlexServer
                plex = PlexServer(os.environ["PLEX_URL"], os.environ["PLEX_TOKEN"])

    else:
        logging.error("While you do have the ADVANCED env on, you forgot to set a login method.\n \
                      Your choices are USER_PASS_SERVER or URL_TOKEN. Refer to README for more.\n \
                      Continuing in standard mode...")
        advanced = False


@app.route("/", methods=["POST"])
def webhook_main():
    if request.method != "POST":
        # Ignore
        logging.info("Got a non POST, somehow...")
        return

    if "PLEX_USERNAME" not in os.environ:
        # You need to have a set Plex username
        logging.critical("You did not set a `PLEX_USERNAME` environment variable.\n\
        Please set it to the Plex username that you want to track.")
        return

    # I don't know what this does,
    # but it helps turn it into a JSON.
    # But I copied it from some other project,
    # I think it was Tautulli.
    data = request.form

    # Fully convert into JSON
    try:
        webhook = json.loads(data["payload"])
    except Exception as e:
        logging.critical("Failed to convert Plex Webhook into JSON")
        logging.error(e)
        return

    # Parsing the Plex Webhook
    try:
        scrobble = parse_plex(webhook_json=webhook)
    except NotImplementedError:
        logging.info("User paused song... Stopping \"Now Playing\" not supported.")

    # If LB_API_TOKEN is set, run scrobble through LB stack
    if ("LB_API_TOKEN" in os.environ) and (scrobble["status"] in ["playing", "scrobbled"]):
        logging.info("Submitting Scrobble to ListenBrainz")
        try:
            submit_lb(scrobble=scrobble)
        except Exception as e:
            logging.error("Encountered an error while submitting to ListenBrainz...")
            logging.error(e)
    else:
        logging.info("Looks like ListenBrainz API Token was not set! Did not submit to LB!")

    # Submitting to LFM
    try:
        if ("LFM_API_SECRET" in os.environ) and (scrobble["status"] in ["playing", "scrobbled"]):
            submit_lfm(network=network, scrobble=scrobble)
    except Exception as e:
        logging.info("Failed to upload scrobble to LastFM. User may not have it configured correctly.")
        logging.info(e)

    return {"status": 200}


app.run(host='0.0.0.0', port=1841)
