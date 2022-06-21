# OfflineTagger

The **OfflineTagger**, or Manual Tagger, is a python command-line tool that creates automatic timestamps during a YouTube or Twitch stream.

---

## Installation
Simply clone the repository or download the Python file directly.
```
git clone https://github.com/WishfulVT/OfflineTagger
```
Once you have the file, run it from within the command-line with `python manual_tagger.py`, or just launch Python's IDLE if you're a light mode enthusiast ~~like me~~.

The manual_tagger.py file was written and tested in Python 3.10, but should be compatible with Python 3.7 and up.

The sole dependency of manual_tagger is the datetime module.

---

## Using the tagger

####Creating timestamps
Once the program is running, simply type any string, so long as it isn't preceded by the '!' key. 
The timestamp will be automatically generated based on the start time, which is determined at program launch. If that's inaccurate, see **Offsetting tags**.

####Adjusting tags
Type `!adjust t` with t being a time in seconds. The latest tag will have its time adjusted cumulatively by t.
Additionally, the `!adjust_back index t` command can adjust any tag, not just the latest. The latest tag is at `index` 1, and the earliest created tag is at `index` n.

####Editing tags
Type `!edit text` with text being any string. You don't have to cap the string in quotes, though you may still do so if you're tagging a quote.
As before, the `!edit_back index text` command adjusts the tag at index `index` (with 1 being the latest tag)
!adjust and !edit are internally one command, but it is impossible to execute both functions simultaneously. Just adjust and then edit, or vice versa.

####Deleting tags
Tags CANNOT be disabled, though they can be deleted. `!delete` with no arguments, or `!delete_back index` with a valid index will delete the latest tag/tag at `index` respectively.
Tags cannot be salvaged once deleted, however the timestamp and tag's current text are outputted on tag deletion so you can simply add the tag back and adjust it into place.

####Offsetting tags
Offsets are identical to adjusting over a range of tags, given as follows: `!offset lower delta (upper)` will adjust all tags from \[lower, upper) by the same time delta of `delta`.
Offsets are not stored in the tagger, and instead act on a tag's time object directly.

####Printing the tags
Use `!flush` to print all tags (with the most recent timestamp and text) to the console. If you pester me about it I'll create a text-file output redirect for this command.
Using !flush will also allow you to exit the program, as will `!quit` and `!exit`, though the latter two will flag you if any tags have been created before you quit the program.
