import math
import calendar
import fpdf


def create_pdf(save_fname, year_first, month_first, year_last=None, month_last=None, events=None, settings=None):
    """\
    Creates a PDF with monthly calenders in it

    Saves the result to save_fname.

    year_first and year_last are integers which specify the first and last year from which to print months.
    month_first is an integer which specifies the first month in year_first to print. Value must be between 1 and 12 inclusive.
    month_last is an integer which specifies the last month in year_last to print. Value must be between 1 and 12 inclusive.

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
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False, 0)

    for year in range(year_first, year_last + 1):
        first_month_in_this_year = 1 if (year > year_first) else month_first
        last_month_in_this_year = 12 if (year < year_last) else month_last

        for month in range(first_month_in_this_year, last_month_in_this_year + 1):
            month_events = events.get(year, {}).get(month, {})
            add_month_to_pdf(pdf, year, month, month_events, settings)
    
    pdf.output(save_fname, "F")


def add_month_to_pdf(pdf, year, month, events=None, settings=None):
    calendar.setfirstweekday(calendar.SUNDAY)

    if settings is None:
        settings = {}
    
    pdf.add_page()

    # Title
    pdf.set_font(
        family = settings.get("title-font-family", "helvetica"), 
        style  = settings.get("title-font-style", "b"), 
        size   = settings.get("title-size", 16), 
    )
    pdf.set_text_color(
        *settings.get("title-color", settings.get("font-color", (0,0,0) ))
    )

    left_margin   = settings.get("margin-left",   0.5)
    right_margin  = settings.get("margin-right",  0.5)
    top_margin    = settings.get("margin-top",    0.3)
    bottom_margin = settings.get("margin-bottom", 0.3)

    # Assuming orientation="landscape" and format="letter", we have these dimensions:
    page_width = 11
    page_height = 8.5

    title_height = settings.get("title-height", 0.25)
    header_height = settings.get("header-height", 0.35)

    usable_width  = page_width  - left_margin - right_margin
    usable_height = page_height - top_margin  - bottom_margin - title_height - header_height

    first_weekday, num_days = calendar.monthrange(year, month)
    first_weekday = (first_weekday + 1) % 7 + 1  # Deal with Mon=0, Sun=6 issue, and shift it to 1-based instead of 0-based

    num_weeks = 1 + math.ceil(
        (num_days - 7 + first_weekday - 1) / 7
    )

    day_vsep = settings.get("day-vsep", 0.1)
    day_hsep = settings.get("day-hsep", 0.1)

    day_width = (usable_width - 6*day_hsep) / 7
    day_height = (usable_height - (num_weeks - 1)*day_vsep) / num_weeks

    title_text = "{}, {}".format(calendar.month_name[month], year)
    pdf.set_xy(x=left_margin, y=top_margin)
    pdf.cell(w=usable_width, h=title_height, txt=title_text, border="", align="C")

    header_area_y = top_margin + title_height
    
    pdf.set_font(
        family = settings.get("header-font-family", "helvetica"), 
        style  = settings.get("header-font-style", "i"), 
        size   = settings.get("header-size", 10), 
    )
    pdf.set_text_color(
        *settings.get("header-color", settings.get("font-color", (0,0,0) ))
    )
    for day_of_week in range(0, 7):
        header_x = left_margin + day_of_week*day_width  + max(0, day_of_week - 1)*day_hsep
        header_text = calendar.day_name[day_of_week - 1]  # -1 to wrap Sunday to front of list
        pdf.set_xy(x=header_x, y=header_area_y)
        pdf.cell(w=day_width, h=header_height, txt=header_text, border="", align="C")

    date_area_x = left_margin
    date_area_y = header_area_y + header_height

    cell_left_margin   = settings.get("margin-cell-left",   0.05)
    cell_top_margin    = settings.get("margin-cell-top",    0.1)

    date = 1
    weekday = first_weekday
    weeknum = 1
    while date <= num_days:
        day_x = date_area_x + (weekday - 1)*day_width  + (weekday - 2)*day_hsep
        day_y = date_area_y + (weeknum - 1)*day_height + (weeknum - 2)*day_vsep
        day_text = "{}".format(date)
        
        font_size = settings.get("date-size", 14)
        font_height_inches = font_size / 72

        pdf.set_font(
            family = settings.get("date-font-family", "helvetica"), 
            style  = settings.get("date-font-style",  "b"), 
            size   = font_size, 
        )
        pdf.set_text_color(
            *settings.get("date-color", settings.get("font-color", (0,0,0) ))
        )
        pdf.set_xy(x=day_x, y=day_y)
        pdf.cell(w=day_width, h=day_height, border="LT", align="L", fill=0)

        pdf.text(
            x = day_x + cell_left_margin, 
            y = day_y + cell_top_margin + font_height_inches/2, 
            txt = day_text, 
        )
        
        event_y = day_y + cell_top_margin + font_height_inches
        for details, style in events.get(date, {}).items():
            detail_lines = details.split("\n")
            size = style.get("font-size", settings.get("event-font-size", 10))
            pdf.set_font(
                family = style.get("font-family", settings.get("event-font-family", "helvetica")), 
                style = style.get("font-style", settings.get("event-font-style", "i")), 
                size = size, 
            )
            pdf.set_text_color(
                *style.get("color", settings.get("event-color", (0,0,0) ))
            )

            event_y += style.get("pts-before", settings.get("event-pts-before", 0)) / 72

            for line in detail_lines:
                pdf.text(
                    x = day_x + cell_left_margin, 
                    y = event_y + size/144, 
                    txt = line, 
                )

                event_y += size/72
            
            event_y += style.get("pts-after", settings.get("event-pts-after", 0)) / 72

        date += 1

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
                    "Events everywhere!" : {}, 
                }
            }, 
            4: {  # Month
                1: {  # Date
                    "More and more of them!" : {}, 
                    "Goodness me!" : {}, 
                }
            }
        }
    }
    create_pdf(save_fname="test.pdf", year_first=2020, month_first=2, month_last=5, events=events)