#Python 3.10
#Version 1.1

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import DefaultCredentialsError
import datetime

# TagTime objects hold a tag's displayed time, as (H:)MM:SS
# It also stores the raw value of its displayed time in seconds
# Additional methods exist to enable comparison/sorting
class TagTime:
    def __init__(self, tagtime, sectime):
        self.tagtime = tagtime
        self.sectime = sectime

    def __lt__(self, other):
        try:
            return self.sectime < other.sectime
        except (AttributeError, TypeError):
            return NotImplemented

    def __eq__(self, other):
        try:
            return self.sectime == other.sectime
        except (AttributeError, TypeError):
            return NotImplemented

    def __hash__(self):
        return hash(self.sectime)

# Takes a time in seconds and converts it to (H:)MM:SS format
def format_tagtime(sectime):
    tagtime = ""
    if sectime < 0:
        tagtime = "-"
        sectime *= -1
    hrs = sectime // 3600
    mins = sectime % 3600 // 60
    secs = sectime % 60
    tagtime += (str(hrs) + ":") if hrs > 0 else ""
    tagtime += ("0" + str(mins) + ":") if mins < 10 else str(mins) + ":"
    tagtime += ("0" + str(secs)) if secs < 10 else str(secs)
    # I miss the old ?/: ternary operators
    return tagtime

# Takes a datetime.timedelta object, converts it to seconds, and also
# returns the above function's formatted time object
def tagtime_times(dt):
    sectime = int(dt.total_seconds())
    tagtime = format_tagtime(sectime)
    return tagtime, sectime

# Flushes tags to the console
def print_tags():
    print("----")
    for tagtime_obj in sorted(tag_dict):
        print(tagtime_obj.tagtime + " " + tag_dict[tagtime_obj])
    print("----")

# The flush and/or exit command. Prints tags, asks if you're finished or
# not. To exit type any string starting with 'y', 'q', or 'e'
def flush_tags(start_with_flush):
    if start_with_flush:
        print_tags()

    exit_char = input("Finished? ").lower()[:1]
    if exit_char in ["y", "q", "e"]:
        ntags = len(tag_dict.keys())
        if not start_with_flush and ntags > 0:
            sure_char = input(f'Are you sure? {str(ntags)} tags are still loaded. ')[:1]
            if sure_char in ["y", "q", "e"]:
                return False
        else:
            return False
    return True

# Adds tags to the dict in such a way that no two tags land on the same
# timestamp. In the case of a conflict, the tag to be added will be placed
# on the first unoccupied second on or after the specified time
def add_tag(tagtime, text):
    cur_sec = tagtime.sectime
    MAXINT = 24*3600
    # O(MAXINT) worst case if every single second there is a tag
    # realistically this is O(1), there is no tag at the current second
    while(cur_sec < MAXINT):
        if tagtime not in tag_dict.keys():
            tag_dict[tagtime] = text
            return tagtime.tagtime
            cur_sec += 24*3600 # exits loop
        else:
            cur_sec += 1
            tagtime = TagTime(format_tagtime(cur_sec), cur_sec)
    return -1

# Adjusts the tag at a given index from the end of the dict, often 1
# which is the latest tag
# Adjusts either change the timestamp (tag_delta), or they change
# the tag's text (this is really an edit)
def adjust_tag(tag_index, tag_delta, new_text):
    ind = int(len(tag_dict.keys()) - tag_index)
    if tag_index < 1 or tag_index > len(tag_dict.keys()):
        print(f'Tag at index {str(ind)} not found')
        return -1

    tagtime = None
    counter = 1
    # O(n) to find the tag we're looking for in the worst case
    # O(1) optimal though since we often adjust the last tag
    for key in reversed(sorted(tag_dict.keys())):
        if tag_index == counter:
            tagtime = key
            break
        counter += 1
    if tagtime == None:
        print(f'Tag at index {str(ind)} not found')
        return -1

    # We have located the tagtime of the tag at index tag_index
    
    if tag_delta != 0:
        # if we are adjusting a tag's time, remove the old timestamp,
        tag_text = tag_dict.pop(tagtime)
        new_sectime = tagtime.sectime + tag_delta
        new_tagtime = TagTime(format_tagtime(new_sectime), new_sectime)

        add_tag(new_tagtime, tag_text) # and add the tag at the new time
        print(f'Tag at {tagtime.tagtime} now at {new_tagtime.tagtime}')
        return tag_index
    else:
        # if we are simply editing a tag's text, pop the old tag
        tag_text = tag_dict.pop(tagtime)
        add_tag(tagtime, new_text) # and use its TagTime to add the replacement
        text_desc = new_text[:16] + "..." if len(new_text) > 16 else new_text
        print(f'Tag at {tagtime.tagtime} now reads \'{text_desc}\'')
        return tag_index

# Adjusts multiple tags by the same amount. Offsets are equivalent to calling
# adjusts on all tags within the [lower, upper) range as specified in the
# command, and adjusts aren't stored anywhere the way they are in other
# tagging tools.
def offset_tags(lower, delta, upper = 24*3600):
    tags_adjusted = 0
    tagtimes_to_adjust = list()
    
    if delta > 0:
        # positive offset: move tags from the back to the front, in order
        # to minimize collisions (see add_tag)
        for tagtime in reversed(sorted(tag_dict.keys())):
            if lower <= tagtime.sectime and tagtime.sectime < upper:
                tagtimes_to_adjust.append(tagtime)
    elif delta < 0:
        # negative offset: move tags in the forwards direction in order to
        # minimize collisions
        for tagtime in sorted(tag_dict.keys()):
            if lower <= tagtime.sectime and tagtime.sectime < upper:
                tagtimes_to_adjust.append(tagtime)

    # Now outside of the tag_dict key loop, adjust each tag in the range
    for tagtime in tagtimes_to_adjust:
        text = tag_dict.pop(tagtime)
        new_sectime = int(tagtime.sectime) + delta
        new_tagtime = TagTime(format_tagtime(new_sectime), new_sectime)
        ret = add_tag(new_tagtime, text)
        if ret != -1:
            tags_adjusted += 1

    return tags_adjusted

# My one piece of code reuse, since I didn't want to overload adjust_tag
# It deletes a tag at a given index from the end, again with 1 being the
# most common argument and targeting the latest tag for deletion
def delete_tag(index):
    ind = int(len(tag_dict.keys()) - index)
    if index < 1 or index > len(tag_dict.keys()):
        print(f'Tag at index {str(ind)} not found')
        return -1

    tagtime = None
    counter = 1
    for key in reversed(sorted(tag_dict.keys())):
        if index == counter:
            tagtime = key
            break
        counter += 1
    if tagtime == None:
        print(f'Tag at index {str(ind)} not found')
        return -1

    tt = tag_dict.pop(tagtime)
    print(f'Deleted tag: {tagtime.tagtime} {tt}')
    return ind

# Takes a YouTube URL and returns only the identifier
def trim_yt_url(URL):
    if "youtu.be" in str(URL):
        return str(URL.split("youtu.be/")[1][:11])
    elif "youtube.com/watch?v=" in str(URL):
        return str(URL.split("youtube.com/watch?v=")[1][:11])
    return URL

# Retrieves the actual start time of a youtube URL. See the SDU
# for similar code.
def get_yt_start_time(URL, api_key = ""):
    if len(api_key) < 1:
        api_key = str(input("Enter your API key:\n"))
    try:
        youtube = build('youtube', 'v3', developerKey = api_key)
        request =  youtube.videos().list(
            part='liveStreamingDetails',
            id=URL
        )
        response = request.execute()
        
        # The response contains a dictionary of items. We care
        # about 'actualStartTime' and nothing else.
        if response == None or len(response['items']) == 0:
            print("Youtube URL/ID not found")
            return None
        elif "liveStreamingDetails" not in response['items'][0] or "actualStartTime" not in response['items'][0]["liveStreamingDetails"]:
            print(f'No stream start time found for ID {URL}')
            return None
        else:
            return response['items'][0]["liveStreamingDetails"]["actualStartTime"]
        
    except (HttpError, DefaultCredentialsError):
        print("YouTube URL/ID not found or invalid API key")
        return None

# Returns a new starttime datetime based on a youtube URL/ID
def adjust_start(URL, api_key, starttime):
    new_start_string = get_yt_start_time(URL, api_key)
    if new_start_string == None:
        return starttime
    # The YT API gives us a string representing a time in UTC
    # The format is 'yyyy-mm-ddThh:mm:ddZ'

    new_start_s2 = str(new_start_string) + "+0000" # Format as UTC, then parse
    new_start = datetime.datetime.strptime(new_start_s2,
                                                "%Y-%m-%dT%H:%M:%SZ%z")

    if new_start == None:
        return starttime
    else:
        # Now that we have new_start, adjust the start time
        new_delta = starttime - new_start
        as_sec = int(new_delta.total_seconds())
        print(f'Start time adjusted by {str(as_sec)}')
              #+ f', from {str(starttime)} to {new_start}')
        
        tag_n = len(tag_dict.keys())
        if tag_n > 0 and abs(as_sec) > 2:
            sure_char = input(f'Adjust {str(tag_n)} existing tags? ').lower()[:1]
            if sure_char in ['y']:
                offset_n = offset_tags(-24*3600, int(as_sec))
                print(f'{str(as_sec)} second offset applied to {str(offset_n)} tags')
            else:
                print(f'{str(tag_n)} tags not adjusted')
        return new_start


## main method execution


starttime = datetime.datetime.now(datetime.timezone.utc)
tag_dict = {}

active = True
while active:
    cur_string = input("")

    # commands start with the ! key
    if(len(cur_string) > 1 and cur_string[0] == '!'):
        command_parts = cur_string[1:].split(" ")
        cmd_word = command_parts[0].lower()
        if cmd_word == "flush":
            active = flush_tags(True)
        elif cmd_word == "quit" or cmd_word == "exit":
            active = flush_tags(False)
        
        elif cmd_word == "adjust":
            try:
                adjval = int(command_parts[1])
                adjust_tag(1, adjval, "")
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !adjust seconds')
        elif cmd_word == "adjust_back":
            try:
                adjval = int(command_parts[2])
                adj_index = int(command_parts[1])
                adjust_tag(adj_index, adjval, "")
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !adjust_back index_from_end seconds')
        elif cmd_word == "edit":
            try:
                unused = str(command_parts[1]) # exclusively triggers index-error/# arguments
                newtext = str(cur_string[6:])
                adjust_tag(1, 0, newtext)
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !edit tag_text')
        elif cmd_word == "edit_back":
            try:
                unused = str(command_parts[2])
                adj_index = int(command_parts[1])
                newtext = str(cur_string[(12+len(str(adj_index))):])
                adjust_tag(adj_index, 0, newtext)
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !edit_back index_from_end tag_text')
        elif cmd_word == "offset":
            try:
                upper_bound = int(command_parts[3]) if len(command_parts) > 3 else 24*3600
                offset_amt = int(command_parts[2])
                lower_bound = int(command_parts[1])
                to = offset_tags(lower_bound, offset_amt, upper_bound)
                print(f'{str(offset_amt)} second offset applied to {str(to)} tags')
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !offset lower_bound offset_seconds (optional: upper_bound)')
        elif cmd_word == "delete":
            delete_tag(1)
        elif cmd_word == "delete_back":
            try:
                del_index = int(command_parts[1])
                delete_tag(del_index)
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !delete_back index_from_end')
        elif cmd_word == "yt_start":
            try:
                url_id = trim_yt_url(str(command_parts[1]))
                API_KEY = "" ### Place your API key here!
                starttime = adjust_start(url_id, API_KEY, starttime)
            except (IndexError, ValueError):
                print(f'Invalid argument(s). Format: !yt_start yt_url')
        else:
            print("Invalid command")

    # any text entered without ! is assumed to be a tag           
    else:
        ct = datetime.datetime.now(datetime.timezone.utc) - starttime
        # ct is a timedelta, not a datetime
        tt, st = tagtime_times(ct) # now they are a formatted string and int
        real_tagtime = add_tag(TagTime(tt, st), cur_string)
        print(real_tagtime + " " + cur_string)

# If you're stuck in the main loop, call !flush and then type "no"
