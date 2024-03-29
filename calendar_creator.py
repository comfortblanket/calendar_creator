import math
import calendar

import datetime
import argparse
import json

# https://pyfpdf.readthedocs.io/en/latest/index.html
import fpdf


__doc__ = """\
A quick and somewhat dirty set of Python functions to create somewhat customizable and printable PDF calendars with custom events
"""

######################################################################
# PDF helper functions

def pdf_get_font_size(pdf):
    """\
    Get the pdf's current font size in points (1 point = 1/72 inches)
    """
    return pdf.font_size_pt


def pdf_set_font(pdf, family, style, size, color):
    """\
    Combine call to pdf.set_font with call to pdf.set_text_color

    Standard available fonts (others can be added -- see fpdf docs):
        courier,   courierB,   courierI,   courierBI
        helvetica, helveticaB, helveticaI, helveticaBI
        times,     timesB,     timesI,     timesBI
        symbol
        zapfdingbats
    """
    pdf.set_font(family=family, style=style, size=size)
    pdf.set_text_color(*color)


def pdf_cell(pdf, x, y, w, h=0, txt="", border=0, ln=0, align="", fill=0, link=''):
    """\
    Combine call to pdf.set_xy with call to pdf.cell
    """
    pdf.set_xy(x=x, y=y)
    pdf.cell(w=w, h=h, txt=txt, border=border, ln=ln, align=align, fill=fill, link=link)


def pdf_text(pdf, x, y, txt, align="L"):
    """\
    Draw text in the given pdf at position x,y with alignment L(eft), C(enter), or R(ight).

    If using align="L", text is drawn with x,y as the top left corner.
    If using align="C", text is drawn with x,y as the top middle of the text.
    If using align="R", text is drawn with x,y as the top right of the text.
    """
    align_adjust = 0

    if align == "C":
        align_adjust = pdf.get_string_width(txt) / 2
    elif align == "R":
        align_adjust = pdf.get_string_width(txt)
    
    font_size_pt = pdf_get_font_size(pdf)

    pdf.text(x=x-align_adjust, y=y+font_size_pt/144, txt=txt)

######################################################################
# Settings and default values

def create_settings(settings):
    created_settings = {
        "margin-left" : 0.5, 
        "margin-right" : 0.5, 
        "margin-top" : 0.3, 
        "margin-bottom" : 0.3, 

        "title-size" : 16, 
        "title-height" : 16 / 72, 
        "title-font-family" : "helvetica", 
        "title-font-style" : "b", 

        "header-size" : 10, 
        "header-height" : 10 / 72, 
        "header-font-family" : "helvetica", 
        "header-font-style" : "i", 

        "day-vsep" : 0.1, 
        "day-hsep" : 0.1, 

        "margin-cell-left" : 0.05, 
        "margin-cell-right" : 0, 
        "margin-cell-top" : 0.1, 
        "margin-cell-bottom" : 0, 

        "date-size" : 14, 
        "date-font-family" : "helvetica", 
        "date-font-style" : "b", 

        "event-font-size" : 8, 
        "event-font-family" : "helvetica", 
        "event-font-style" : "i", 
        "event-color" : (0,0,0), 
        "event-pts-before" : 0, 
        "event-pts-after" : 0, 
        
        "special-event-font-size" : 6, 
        "special-event-font-family" : "helvetica", 
        "special-event-font-style" : "", 
        "special-event-color" : (0,0,0), 
        "special-event-pts-before" : 0, 
        "special-event-pts-after" : 0, 
    }

    created_settings.update(settings)

    if "font-color" not in created_settings:
        created_settings["font-color"] = (0,0,0)

    font_color = created_settings["font-color"]

    for color_key in ["title-color", "header-color", "date-color"]:
        if color_key not in created_settings:
            created_settings[color_key] = font_color
    
    return created_settings


def create_event_style(style, settings):
    special = style.get("special", "normal")
    is_special = special in ("header", "footer")
    is_header = special == "header"
    
    created_style = {
        "special" : special, 

        "font-size" : settings["special-event-font-size"] if is_special else settings["event-font-size"], 
        "font-family" : settings["special-event-font-family"] if is_special else settings["event-font-family"], 
        "font-style" : settings["special-event-font-style"] if is_special else settings["event-font-style"], 
        "color" : settings["special-event-color"] if is_special else settings["event-color"], 
        "pts-before" : settings["special-event-pts-before"] if is_special else settings["event-pts-before"], 
        "pts-after" : settings["special-event-pts-after"] if is_special else settings["event-pts-after"], 

        "halign" : "C" if is_header else "L", 
        "adjust-x-pts" : 0, 
        "adjust-y-pts" : -72*settings["margin-cell-top"]/2 if is_header else 0, 
        "increment-line" : True, 
    }

    created_style.update(style)

    return created_style

######################################################################
# Central functionality


def year_month_gen(year_first, month_first, year_last=None, month_last=None):

    assert year_last is None or (year_first <= year_last), \
        "year_last must be None, or else no smaller than year_first"
    assert 0 < month_first <= 12, \
        "month_first should be in a value from 1 to 12 inclusive"
    assert month_last is None or (0 < month_last <= 12), \
        "month_last must be None, or else should be in a value from 1 to 12 inclusive"

    if year_last is None:
        year_last = year_first
    
    if month_last is None:
        month_last = month_first

    for year in range(year_first, year_last + 1):
        first_month_in_this_year = 1 if (year > year_first) else month_first
        last_month_in_this_year = 12 if (year < year_last) else month_last

        for month in range(first_month_in_this_year, last_month_in_this_year + 1):
            yield (year, month)

def create_calendar_pdf(save_fname, year_first, month_first, year_last=None, month_last=None, events=None, settings=None):
    """\
    Creates a PDF with monthly calenders in it

    Saves the result to save_fname.

    year_first and year_last are integers which specify the first and last year from which to print months.
    month_first is an integer which specifies the first month in year_first to print. Value must be between 1 and 12 inclusive.
    month_last is an integer which specifies the last month in year_last to print. Value must be between 1 and 12 inclusive.

    settings is a dict which has the following options in it, with default values in parentheses:
    
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

    events is a dict of the following example structure:
    {
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
                1: {  # Date
                    "More and more of them!" : {}, 
                }
            }
        }
    }

    Each event maps to another dict so the style for that event can be 
    changed. Each of these dicts has the following options, with default 
    values in parentheses (many defaults come from the settings dict 
    above):

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
        increment-line (True) whether to increment the line count after writing out the text of this event
    
    Note that special events are simply regular events with slightly different 
    defaults. "header" events are placed in the date cell in a column which 
    begins to the right of the date's number, instead of below it. "footer" 
    events begin at the bottom of the date cell, and sequential ones move 
    upward instead of down. These events are tracked separately from regular 
    events, and so they can easily overlap with each other if you have too 
    many special events and you don't adjust positions.
    """

    if events is None:
        events = {}

    settings = create_settings({} if settings is None else settings)

    pdf = fpdf.FPDF(orientation="landscape", unit="in", format="letter")
    pdf.set_margins(0, 0, 0)  # Left, top, right
    pdf.set_auto_page_break(False, 0)  # Bottom
    
    # Assuming orientation="landscape" and format="letter", we have these dimensions:
    page_width = 11
    page_height = 8.5

    for year, month in year_month_gen(year_first, month_first, year_last, month_last):
        month_events = events.get(year, {}).get(month, {})
        add_month_page_to_pdf(pdf, year, month, month_events, settings, page_width, page_height)
    
    pdf.output(save_fname, "F")


def add_month_page_to_pdf(pdf, year, month, events=None, settings=None, page_width=11, page_height=8.5):
    """\
    Assumes units are in inches.

    +------------------------ page_width ------------------------+
    |                          <TITLE>                           top_margin
    |  +-------------------- usable_width --------------------+  |
    |  |  <HEADER1>  <HEADER2> ................... <HEADER7>  header_height
    |  +------------------------------------------------------+  |
    |  |                                                      |  |
    |  |                                                      |  |
    |  |                                                      |  |
    |  |                                                      |  page_height
    |  usable_height         <DATE AREA>                      |  |
    |  |                                                      |  |
    |  |                                                      |  |
    |  |                                                      |  |
    |  |                                                      |  |
    |  +------------------------------------------------------+  |
    |                                                            bottom_margin
    +------------------------------------------------------------+
    """
    
    calendar.setfirstweekday(calendar.SUNDAY)

    if settings is None:
        settings = create_settings({})
    
    pdf.add_page()

    # Page margins
    left_margin   = settings["margin-left"]
    right_margin  = settings["margin-right"]
    top_margin    = settings["margin-top"]
    bottom_margin = settings["margin-bottom"]

    usable_width  = page_width  - left_margin - right_margin
    usable_top_y = top_margin

    # Title

    title_font_size = settings["title-size"]
    title_height = settings["title-height"]
    title_text = "{} {}".format(calendar.month_name[month], year)

    # DRAW title
    pdf_set_font(
        pdf, 
        family = settings["title-font-family"], 
        style  = settings["title-font-style"], 
        size   = title_font_size, 
        color  = settings["title-color"], 
    )
    pdf_text(
        pdf, 
        x = left_margin + usable_width/2, 
        y = usable_top_y, 
        txt = title_text, 
        align = "C", 
    )

    usable_top_y += title_height

    # Header

    header_font_size = settings["header-size"]
    header_height = settings["header-height"]
    header_width = usable_width / 7  # Width of individual day-of-week header title boxes
    
    # DRAW header
    pdf_set_font(
        pdf, 
        family = settings["header-font-family"], 
        style  = settings["header-font-style"], 
        size   = header_font_size, 
        color  = settings["header-color"], 
    )
    for day_of_week in range(0, 7):
        header_x = left_margin + day_of_week*header_width
        header_text = calendar.day_name[day_of_week - 1]  # -1 to wrap Sunday to front of list
        pdf_text(
            pdf, 
            x = header_x + header_width/2, 
            y = usable_top_y, 
            txt = header_text, 
            align = "C", 
        )

    usable_top_y += header_height

    # Date area

    first_weekday, num_days = calendar.monthrange(year, month)

    # Deal with Mon=0, Sun=6 issue, and shift it to 1-based instead of 0-based
    first_weekday = (first_weekday + 1) % 7 + 1

    # Number of distinct weeks spanned by days in this month
    num_weeks = 1 + math.ceil(
        (num_days - 7 + first_weekday - 1) / 7
    )

    # Height usable by actual calendar area
    usable_height = page_height - usable_top_y - bottom_margin

    # Separation between days
    day_vsep = settings["day-vsep"]
    day_hsep = settings["day-hsep"]
    
    # Dimensions of each day - split up usable space
    day_width = (usable_width - 6*day_hsep) / 7
    day_height = (usable_height - (num_weeks - 1)*day_vsep) / num_weeks
    
    # Coordinates of top left of date area
    date_area_x = left_margin
    date_area_y = usable_top_y

    # Margins for text inside the date cell
    cell_left_margin    = settings["margin-cell-left"]
    cell_right_margin   = settings["margin-cell-right"]
    cell_top_margin     = settings["margin-cell-top"]
    cell_bottom_margin  = settings["margin-cell-bottom"]
    cell_margins = (
        cell_left_margin, 
        cell_right_margin, 
        cell_top_margin, 
        cell_bottom_margin, 
    )

    # Counter variables for the loop
    date = 1 
    weekday = first_weekday
    weeknum = 1

    # We're going to loop date from 1 to the last date in the month (eg. 30 for April)
    while date <= num_days:

        # Top left coordinate of date
        day_x = date_area_x + (weekday - 1)*(day_width + day_hsep)
        day_y = date_area_y + (weeknum - 1)*(day_height + day_vsep)

        # DRAW date lines
        pdf.line(day_x, day_y, day_x+day_width, day_y)
        pdf.line(day_x, day_y, day_x, day_y+day_height)

        # Date number
        day_text = "{}".format(date)
        font_size = settings["date-size"]
        font_height_inches = font_size / 72

        # DRAW date number
        pdf_set_font(
            pdf, 
            family = settings["date-font-family"], 
            style  = settings["date-font-style"], 
            size   = font_size, 
            color  = settings["date-color"], 
        )
        header_event_x = day_x + cell_left_margin + pdf.get_string_width(day_text)
        header_event_width = day_x + day_width - header_event_x
        pdf_text(
            pdf, 
            x = day_x + cell_left_margin, 
            y = day_y + cell_top_margin, 
            txt = day_text, 
            align = "L", 
        )
        
        # Events for this date

        # These will be updated as we draw each event, and are in inches (like most things)
        event_y = day_y + cell_top_margin + font_height_inches
        header_event_y = day_y + cell_top_margin
        footer_event_y = day_y + day_height - cell_bottom_margin

        for details, specific_style in events.get(date, {}).items():
            style = create_event_style(specific_style, settings)

            if style["special"] == "header":
                header_event_y = draw_event(pdf, header_event_x, header_event_width, details, style, header_event_y, cell_margins)
            elif style["special"] == "footer":
                footer_event_y = draw_event_upward(pdf, day_x, day_width, details, style, footer_event_y, cell_margins)
            else:
                event_y = draw_event(pdf, day_x, day_width, details, style, event_y, cell_margins)

        # Now we'll move on to the next date
        date += 1

        # Wrap weekdays and weeks
        if weekday == 7:
            weekday = 1
            weeknum += 1
        else:
            weekday += 1


def draw_event(pdf, day_x, day_width, details, style, event_y, cell_margins):
    
    # Adjust extra space before the event
    event_y += style["pts-before"] / 72

    # Margins for text inside the date cell
    (
        cell_left_margin, 
        cell_right_margin, 
        cell_top_margin, 
        cell_bottom_margin, 
    ) = cell_margins

    # Amount to special-adjust the position for this event
    adjust_x = style["adjust-x-pts"] / 72
    adjust_y = style["adjust-y-pts"] / 72

    # Split apart the event details on newlines to get the different lines of text
    detail_lines = details.split("\n")

    # Font size for this event
    size = style["font-size"]
    
    # DRAW event details
    pdf_set_font(
        pdf, 
        family = style["font-family"], 
        style  = style["font-style"], 
        size   = size, 
        color  = style["color"], 
    )
    for line in detail_lines:
        halign = style["halign"]

        if halign == "C":
            text_x = (day_x + cell_left_margin) + (day_width - cell_left_margin - cell_right_margin)/2
        elif halign == "R":
            text_x = (day_x + cell_left_margin) + (day_width - cell_left_margin - cell_right_margin)
        else:  # Left-align
            text_x = (day_x + cell_left_margin)

        pdf_text(
            pdf, 
            x = text_x + adjust_x, 
            y = event_y + adjust_y, 
            txt = line, 
            align = halign, 
        )
        
        # Newline
        event_y += size/72
    
    # After drawing the event, IF we had any lines to draw AND we are 
    # not supposed to increment the line count, then let's back off a 
    # single line. This allows any newlines in the details to be used, 
    # but removes the last one.
    if detail_lines and not style["increment-line"]:
        event_y -= size/72

    # Adjust extra space after the event
    event_y += style["pts-after"] / 72

    return event_y


def draw_event_upward(pdf, day_x, day_width, details, style, event_y, cell_margins):
    """\
    This text drawing is unique, in that the point specified to draw 
    at (day_x, event_y) is the bottom left corner of where the text 
    should be, instead of the top left. This is because we don't 
    know how much to move upward until we know the font (and 
    therefore height) of the text.
    """
    
    # Adjust extra space after (below) the event
    event_y -= style["pts-after"] / 72

    # Margins for text inside the date cell
    (
        cell_left_margin, 
        cell_right_margin, 
        cell_top_margin, 
        cell_bottom_margin, 
    ) = cell_margins

    # Amount to special-adjust the position for this event
    adjust_x = style["adjust-x-pts"] / 72
    adjust_y = style["adjust-y-pts"] / 72

    # Split apart the event details on newlines to get the different lines of text
    detail_lines = details.split("\n")

    # Font size for this event
    size = style["font-size"]
    
    # DRAW event details
    pdf_set_font(
        pdf, 
        family = style["font-family"], 
        style  = style["font-style"], 
        size   = size, 
        color  = style["color"], 
    )
    event_y -= len(detail_lines) * size/72
    for line in detail_lines:

        halign = style["halign"]

        if halign == "C":
            text_x = (day_x + cell_left_margin) + (day_width - cell_left_margin - cell_right_margin)/2
        elif halign == "R":
            text_x = (day_x + cell_left_margin) + (day_width - cell_left_margin - cell_right_margin)
        else:  # Left-align
            text_x = (day_x + cell_left_margin)

        pdf_text(
            pdf, 
            x = text_x + adjust_x, 
            y = event_y + adjust_y, 
            txt = line, 
            align = halign, 
        )
        
        # Newline
        event_y += size/72
    
    event_y -= len(detail_lines) * size/72

    # Adjust extra space before (above) the event
    event_y -= style["pts-before"] / 72

    return event_y

######################################################################
# Example usage

def run_example(outfile="example_output.pdf"):
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
    create_calendar_pdf(save_fname=f"{outfile}", year_first=2020, month_first=2, month_last=5, events=events)


def print_example(outfile="example_output.pdf"):
    import inspect
    example_source = "\n".join(
        line[4:]  # Remove four-space indentation
        for line in 
        inspect.getsource(run_example).split("\n")[1:]  # All but first line of source
    )
    print(example_source.replace("f\"{outfile}\"", f"\"{outfile}\""))

######################################################################
# Commandline functions

def setup_argparser():
    argparser = argparse.ArgumentParser(description=__doc__)
    subparsers = argparser.add_subparsers(
        help="sub-command help", 
    )

    # Example parser

    example_parser = subparsers.add_parser(
        "show-example", 
        aliases = ["example"], 
        help = "show and run an example, then quit", 
    )
    example_parser.set_defaults(subparser_name="show-example")

    example_parser.add_argument(
        "outfile", 
        metavar = "OUT_FILE", 
        default = "example_output.pdf", 
        nargs = "?", 
        type = str, 
        help = "the pdf filename to output", 
    )

    # Normal json parser

    json_parser = subparsers.add_parser(
        "use-json", 
        aliases = ["json"], 
        help = "create calendar based on json input files", 
    )
    json_parser.set_defaults(subparser_name="use-json")

    json_parser.add_argument(
        "outfile", 
        metavar = "OUTPUT", 
        type = str, 
        help = "the pdf filename to output", 
    )
    
    json_parser.add_argument(
        "--events", 
        metavar = "EVENTS", 
        type = str, 
        nargs = "+", 
        default = None, 
        help = "a json events file", 
    )
    
    json_parser.add_argument(
        "--yearly", 
        metavar = "YEARLY", 
        type = str, 
        nargs = "+", 
        default = None, 
        help = "a json events file without years", 
    )
    
    json_parser.add_argument(
        "--settings", 
        metavar = "SETTINGS", 
        type = str, 
        default = None, 
        help = "a json settings file", 
    )

    json_parser.add_argument(
        "--year_first", 
        metavar = "YEAR1", 
        type = int, 
        default = datetime.datetime.today().year, 
        help = "the first year to include in the calendar", 
    )

    json_parser.add_argument(
        "--month_first", 
        metavar = "MONTH1", 
        type = int, 
        default = datetime.datetime.today().month, 
        help = "the first from YEAR1 to include in the calendar", 
    )

    json_parser.add_argument(
        "--year_last", 
        metavar = "YEAR2", 
        type = int, 
        default = None, 
        help = "the last year to include in the calendar", 
    )

    json_parser.add_argument(
        "--month_last", 
        metavar = "MONTH2", 
        type = int, 
        default = None, 
        help = "the last month from YEAR2 to include in the calendar", 
    )

    return argparser


def convert_json_to_dict(json_dict, skip_year=False):

    if skip_year:
        new_year = {}
        for month_str, month_details in json_dict.items():
                new_month = {}

                for day_str, events in month_details.items():
                    if events:
                        new_month[int(day_str)] = events
                
                if new_month:
                    new_year[int(month_str)] = new_month
        
        return new_year
        
    else:
        new_dict = {}
        for year_str, year_dict in json_dict.items():
            new_year = convert_json_to_dict(year_dict, skip_year=True)
            
            if new_year:
                new_dict[int(year_str)] = new_year

        return new_dict


def update_event(events, year, month, day, details, style_dict, remove_first=False):
    if year not in events:
        events[year] = {}
    year_dict = events[year]
    
    if month not in year_dict:
        year_dict[month] = {}
    month_dict = year_dict[month]

    if day not in month_dict:
        month_dict[day] = {}
    day_dict = month_dict[day]

    if remove_first or details not in day_dict:
        day_dict[details] = style_dict
    else:
        day_dict[details].update(style_dict)


def event_items_gen(events):
    for year, year_dict in events.items():
        for month, month_details in year_dict.items():
            for day, events_dict in month_details.items():
                for details, style_dict in events_dict.items():
                    yield (year, month, day, details, style_dict)


def yearly_items_gen(events):
    for month, month_details in events.items():
        for day, events_dict in month_details.items():
            for details, style_dict in events_dict.items():
                yield (month, day, details, style_dict)


def update_event_dict(events, new_dict):
    for (year, month, day, details, style_dict) in event_items_gen(new_dict):
        update_event(events, year, month, day, details, style_dict)


def main(*passed_args):
    argparser = setup_argparser()

    if passed_args:
        args = argparser.parse_args(passed_args)
    else:
        args = argparser.parse_args()

    if args.subparser_name == "show-example":
        print_example(args.outfile)
        run_example(args.outfile)

    elif args.subparser_name == "use-json":
        events = None
        if args.events:
            
            if events is None:
                events = {}
            
            for event_fname in args.yearly:
                with open(event_fname, "r") as fid:
                    yearly = convert_json_to_dict(json.load(fid), skip_year=True)
                
                for year in range(args.year_first, args.year_last + 1):
                    for (month, day, details, style_dict) in yearly_items_gen(yearly):
                            update_event(events, year, month, day, details, style_dict)
            
            for event_fname in args.events:
                with open(event_fname, "r") as fid:
                    update_event_dict(
                        events, 
                        convert_json_to_dict(json.load(fid), skip_year=False), 
                    )

        settings = None
        if args.settings:
            with open(args.settings, "r") as fid:
                settings = convert_json_to_dict(
                    json.load(fid)
                )
        
        create_calendar_pdf(
            args.outfile, 
            args.year_first, 
            args.month_first, 
            args.year_last, 
            args.month_last, 
            events, 
            settings
        )

    else:
        raise ValueError(f"Unknown subcommand '{args.subparser_name}'")

######################################################################

if __name__ == "__main__":
    # main(
    #     "json", 
    #     "--events", "example-events.json", 
    #     "--year_first", "2020", 
    #     "--month_first", "2", 
    #     "--month_last", "5", 
    #     "out.pdf", 
    # )

    # main()

    main(
        "json", 
        "--events", "../monthly_event_fetcher/bj_events_2022.12-2024.01.json", 
        "--yearly", "birthdays.json", 
        "--year_first", "2022", 
        "--month_first", "12", 
        "--year_last", "2024", 
        "--month_last", "1", 
        "calendar_2022.12-2024.01.pdf", 
    )
