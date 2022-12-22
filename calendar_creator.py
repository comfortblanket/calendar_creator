import math
import calendar

# https://pyfpdf.readthedocs.io/en/latest/index.html
import fpdf


def create_calendar_pdf(save_fname, year_first, month_first, year_last=None, month_last=None, events=None, settings=None):
    """\
    Creates a PDF with monthly calenders in it

    Saves the result to save_fname.

    year_first and year_last are integers which specify the first and last year from which to print months.
    month_first is an integer which specifies the first month in year_first to print. Value must be between 1 and 12 inclusive.
    month_last is an integer which specifies the last month in year_last to print. Value must be between 1 and 12 inclusive.

    settings is a dict which has the following options in it, with default values in parentheses:
    
        font-color default value to use for any non-specified font colors
        
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
        margin-cell-top (0.1) padding in inches added to top of day contents
        
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

        font-size (event-font-size)
        font-family (event-font-family)
        font-style (event-font-style)
        color (event-color)
        pts-before (event-pts-before)
        pts-after (event-pts-after)
        
        adjust-x-pts (0) amount in points to adjust placement of text in x direction
        adjust-y-pts (0) amount in points to adjust placement of text in y direction
        increment-line (True) whether to increment the line count after writing out the text of this event
    
    Note that a good starting point for a style to place some small text at 
    the top of a date (given other default values) is:
    {
        "font-size" : 8, 
        "adjust-x-pts" : 25,
        "adjust-y-pts" : -15, 
        "increment-line" : False, 
    }
    """

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

    if events is None:
        events = {}

    pdf = fpdf.FPDF(orientation="landscape", unit="in", format="letter")
    pdf.set_margins(0, 0, 0)  # Left, top, right
    pdf.set_auto_page_break(False, 0)  # Bottom
    
    # Assuming orientation="landscape" and format="letter", we have these dimensions:
    page_width = 11
    page_height = 8.5

    for year in range(year_first, year_last + 1):
        first_month_in_this_year = 1 if (year > year_first) else month_first
        last_month_in_this_year = 12 if (year < year_last) else month_last

        for month in range(first_month_in_this_year, last_month_in_this_year + 1):
            month_events = events.get(year, {}).get(month, {})
            add_month_page_to_pdf(pdf, year, month, month_events, settings, page_width, page_height)
    
    pdf.output(save_fname, "F")


def pdf_set_font(pdf, family, style, size, color):
    pdf.set_font(family=family, style=style, size=size)
    pdf.set_text_color(*color)


def pdf_cell(pdf, x, y, w, h=0, txt="", border=0, ln=0, align="", fill=0, link=''):
    pdf.set_xy(x=x, y=y)
    pdf.cell(w=w, h=h, txt=txt, border=border, ln=ln, align=align, fill=fill, link=link)


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
        settings = {}
    
    pdf.add_page()

    # Page margins
    left_margin   = settings.get("margin-left",   0.5)
    right_margin  = settings.get("margin-right",  0.5)
    top_margin    = settings.get("margin-top",    0.3)
    bottom_margin = settings.get("margin-bottom", 0.3)

    usable_width  = page_width  - left_margin - right_margin
    usable_top_y = top_margin

    # Title

    title_font_size = settings.get("title-size", 16)
    title_height = settings.get("title-height", title_font_size / 72)
    title_text = "{} {}".format(calendar.month_name[month], year)

    # DRAW title
    pdf_set_font(
        pdf, 
        family = settings.get("title-font-family", "helvetica"), 
        style  = settings.get("title-font-style", "b"), 
        size   = title_font_size, 
        color  = settings.get("title-color", settings.get("font-color", (0,0,0) )), 
    )
    pdf_cell(
        pdf, 
        x = left_margin,   y = usable_top_y, 
        w = usable_width,  h = title_height, 
        txt = title_text, 
        border = "",       align = "C", 
    )

    usable_top_y += title_height

    # Header

    header_font_size = settings.get("header-size", 10)
    header_height = settings.get("header-height", header_font_size / 72)
    header_width = usable_width / 7  # Width of individual day-of-week header title boxes
    
    # DRAW header
    pdf_set_font(
        pdf, 
        family = settings.get("header-font-family", "helvetica"), 
        style  = settings.get("header-font-style", "i"), 
        size   = header_font_size, 
        color  = settings.get("header-color", settings.get("font-color", (0,0,0) )), 
    )
    for day_of_week in range(0, 7):
        header_x = left_margin + day_of_week*header_width
        header_text = calendar.day_name[day_of_week - 1]  # -1 to wrap Sunday to front of list
        pdf_cell(
            pdf, 
            x = header_x,     y = usable_top_y, 
            w = header_width, h = header_height, 
            txt = header_text, 
            border = "",      align = "C", 
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
    day_vsep = settings.get("day-vsep", 0.1)
    day_hsep = settings.get("day-hsep", 0.1)
    
    # Dimensions of each day - split up usable space
    day_width = (usable_width - 6*day_hsep) / 7
    day_height = (usable_height - (num_weeks - 1)*day_vsep) / num_weeks
    
    # Coordinates of top left of date area
    date_area_x = left_margin
    date_area_y = usable_top_y

    # Margins for text inside the date cell
    cell_left_margin = settings.get("margin-cell-left", 0.05)
    cell_top_margin  = settings.get("margin-cell-top",  0.1)

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
        font_size = settings.get("date-size", 14)
        font_height_inches = font_size / 72

        # DRAW date number
        pdf_set_font(
            pdf, 
            family = settings.get("date-font-family", "helvetica"), 
            style  = settings.get("date-font-style",  "b"), 
            size   = font_size, 
            color  = settings.get("date-color", settings.get("font-color", (0,0,0) )), 
        )
        pdf.text(
            x = day_x + cell_left_margin, 
            y = day_y + cell_top_margin + font_height_inches/2, 
            txt = day_text, 
        )
        
        # Events for this date

        # This will be updated as we draw each event, and is in inches (like most things)
        event_y = day_y + cell_top_margin + font_height_inches

        for details, style in events.get(date, {}).items():

            # Adjust extra space before the event
            event_y += style.get("pts-before", settings.get("event-pts-before", 0)) / 72

            # Amount to special-adjust the position for this event
            adjust_x = style.get("adjust-x-pts", 0) / 72
            adjust_y = style.get("adjust-y-pts", 0) / 72

            # Split apart the event details on newlines to get the different lines of text
            detail_lines = details.split("\n")

            # Font size for this event
            size = style.get("font-size", settings.get("event-font-size", 10))
            
            # DRAW event details
            pdf_set_font(
                pdf, 
                family = style.get("font-family", settings.get("event-font-family", "helvetica")), 
                style  = style.get("font-style", settings.get("event-font-style", "i")), 
                size   = size, 
                color  = style.get("color", settings.get("event-color", (0,0,0) )), 
            )
            for line in detail_lines:
                pdf.text(
                    x = day_x + cell_left_margin + adjust_x, 
                    y = event_y + size/144 + adjust_y, 
                    txt = line, 
                )
                
                # Newline
                event_y += size/72
            
            # After drawing the event, IF we had any lines to draw AND we are 
            # not supposed to increment the line count, then let's back off a 
            # single line. This allows any newlines in the details to be used, 
            # but removes the last one.
            if detail_lines and not style.get("increment-line", True):
                event_y -= size/72

            # Adjust extra space after the event
            event_y += style.get("pts-after", settings.get("event-pts-after", 0)) / 72

        # Now we'll move on to the next date
        date += 1

        # Wrap weekdays and weeks
        if weekday == 7:
            weekday = 1
            weeknum += 1
        else:
            weekday += 1


if __name__ == "__main__":
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
                    "Another event!" : {}, 
                }
            }, 
            4: {  # Month
                9: {  # Date
                    "Events everywhere!" : {}, 
                }, 
                20: {  # Date
                    "Goodness me!" : {
                        "font-size" : 8, 
                        "adjust-x-pts" : 25,
                        "adjust-y-pts" : -15, 
                        "increment-line" : False, 
                    }, 
                    "More and more of\nthem!" : {}, 
                    "Last one..." : {
                        "pts-before" : 6, 
                    }, 
                }
            }
        }
    }
    create_calendar_pdf(save_fname="test.pdf", year_first=2020, month_first=2, month_last=5, events=events)