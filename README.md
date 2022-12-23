# calendar_creator
A quick and somewhat dirty set of Python functions to create somewhat customizable and printable PDF calendars with custom events.

![example-month](https://user-images.githubusercontent.com/30023105/209266455-29c79d37-70a2-4446-821d-5afdacfc88e5.png)
*A month created by the code in the [Example](#example) section of this Readme*

## Basic Usage

The `create_calendar_pdf`(`save_fname`, `year_first`, `month_first`, `year_last=None`, `month_last=None`, `events=None`, `settings=None`) function creates a PDF with monthly calenders in it. The result is saved to `save_fname`.

`year_first` and `year_last` are integers which specify the first and last year from which to print months.

`month_first` is an integer which specifies the first month in `year_first` to print. `month_last` is an integer which specifies the last month in `year_last` to print. Month values must be between 1 and 12 inclusive.

`settings` is a dict which has the following options in it, with default values in parentheses:

    font-color (0,0,0) default value to use for any non-specified font colors
    
    margin-left (0.5) left page margin in inches
    margin-right (0.5) right page margin in inches
    margin-top (0.3) top page margin in inches
    margin-bottom (0.3) bottom page margin in inches
    
    title-size (16) font size in points
    title-height (title-size converted to inches) vertical space used for the title in inches
    title-font-family (helvetica)
    title-font-style (b)
    title-color (font-color if given, else 0,0,0) tuple of 0-255 r,g,b values
    
    header-size (10) day of week header font size in points
    header-height (header-size converted to inches) vertical space used for day of week headers in inches
    header-font-family (helvetica)
    header-font-style (i)
    header-color (font-color if given, else 0,0,0) tuple of 0-255 r,g,b values
    
    day-vsep (0.1) vertical space separating days on the calendar
    day-hsep (0.1) horizontal space separating days on the calendar
    
    margin-cell-left (0.05) padding in inches added to left of day contents
    margin-cell-right (0) padding in inches added to right of day contents (used with Right and Center aligned text)
    margin-cell-top (0.1) padding in inches added to top of day contents
    margin-cell-bottom (0) padding in inches added to top of day contents (used with special=footer style)
    
    date-color (font-color if given, else 0,0,0) tuple of 0-255 r,g,b values; color for date number
    date-size (14) font size for date number in points
    date-font-family (helvetica)
    date-font-style (b)
    
    event-font-size (10) default event font size
    event-font-family (helvetica) default event font family
    event-font-style (i) default event font style
    event-color (0,0,0) default event font color
    event-pts-before (0) default amount of space in points to insert before an event
    event-pts-after (0) default amount of space in points to insert after an event
    
    special-event-font-size (8) default special event font size
    special-event-font-family (helvetica) default special event font family
    special-event-font-style () default special event font style
    special-event-color (0,0,0) default special event font color
    special-event-pts-before (0) default amount of space in points to insert before a special event
    special-event-pts-after (0) default amount of space in points to insert after a special event

As a general rule, all distances are specified in inches, unless they are specified to be in points (1 point = 1/72 inches).

`events` is a dict with other nested dicts in it, which specify event details. `events` itself has integer years as keys which map to dicts for events in the given year. Each of those dicts has integer months (from 1-12) as keys which map to dicts for events in the given month. Each of those dicts has integer dates (from 1-31) as keys which map to dcits for events on that specific date. And those dicts map string keys which provide the text details of each event to another dict which contains additional style information for that event. To use the default style, just map it to an empty dict. See the below [Example](#example) section for more details.

The event style dicts have the following options, with default values in parentheses (many defaults come from the `settings` dict above):

    special (normal) type of special event- can be normal, header, or footer

    font-size (special-event-font-size if special, else event-font-size)
    font-family (special-event-font-family if special, else event-font-family)
    font-style (special-event-font-style if special, else event-font-style)
    color (special-event-color if special, else event-color)
    pts-before (special-event-pts-before if special, else event-pts-before)
    pts-after (special-event-pts-after if special, else event-pts-after)
    
    halign (C if special=header, else L) horizontal alignment of text in date cell, value can be L, C, or R
    adjust-x-pts (0) amount in points to adjust placement of text in x direction
    adjust-y-pts (-72*(margin-cell-top)/2 if special=header, else 0) amount in points to adjust placement of text in y direction
    increment-line (True) whether to increment the line count after writing out the text of this event (not used with special=footer)

Note that special events are simply regular events with slightly different defaults. "header" events are placed in the date cell in a column which begins to the right of the date's number, instead of below it. "footer" events begin at the bottom of the date cell, and sequential ones move upward instead of down. These events are tracked separately from regular events, and so they can easily overlap with each other if you have too many special events and you don't adjust positions.

### Example

    events = {
        1992: {  # Year
            12: {  # Month
                9: {  # Date
                    # Events:
                    "Today is Dec 9, 1992" : {}, 
                    "Here is another event" : {}, 
                }, 
            }, 
        }, 
        2020: {  # Year
            3: {  # Month
                1: {  # Date
                    "Events everywhere!" : {}, 
                }
            }, 
            4: {  # Month
                9: {  # Date
                    "An event!" : {
                        "halign" : "R", 
                        "color" : (255, 0, 0), 
                        "font-family" : "times", 
                    }, 
                }, 
                20: {  # Date
                    "Goodness me!" : {
                        "special" : "header", 
                    }, 
                    "More and more of\nthem!" : {
                        "halign" : "C", 
                    }, 
                    "Last one..." : {
                        "pts-before" : 6, 
                        "font-style" : "bu", 
                    }, 
                    "Oh wait, one more..." : {
                        "special" : "footer", 
                        "halign" : "R", 
                    }, 
                    "No, this is the last one!" : {
                        "special" : "footer", 
                    }, 
                }
            }
        }
    }
    create_calendar_pdf(save_fname="test.pdf", year_first=2020, month_first=2, month_last=5, events=events)
