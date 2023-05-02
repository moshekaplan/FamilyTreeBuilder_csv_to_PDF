#!/usr/bin/env python

"""
Converts a MyHeritage Family Tree Builder CSV report file into a PDF list of birthdays and anniversaries
"""

import csv
import argparse
import datetime
import calendar
import collections

import reportlab.platypus
import reportlab.lib.styles
import reportlab.lib.units
import reportlab.lib.pagesizes

def normalize_name(row):
    """Last names are tricky. They can either be based on the "Married Name", spouse's name ("Marriage to"), or actual "Last name".
    
    Here's the strategy we'll use:
    * Men: Copy their First + Last name.
    * Women: Spouses last name, if applicable, otherwise Married Name, otherwise last name
    """
    if row['Gender'] == 'M':
        return row['First name'] + ' ' + row['Last name']
    else:
        spouse_last_name = row['Marriage to'].rsplit(' ', 1)
        if len(spouse_last_name) == 2:
            return row['First name'] + ' ' + spouse_last_name[1]
        elif row['Married Name']:
           return row['First name'] + ' ' + row['Married Name']
        else:
            return row['First name'] + ' ' + row['Last name']   

def parse_input(fname):
    with open(fname) as fh:
        reader = csv.DictReader(fh)
        rows = [row for row in reader]

    # Filter out dead people:
    rows = [row for row in rows if not row['Death date']]

    special_days = []

    # List of birthdays
    for row in rows:
        try:
            if row['Birth date']:
                event = {}
                event['date'] = datetime.datetime.strptime(row['Birth date'], "%b. %d %Y")
                event['reason'] = "Birthday of %s (born in %s)" % (normalize_name(row), event['date'].year)
                special_days.append(event)
        except:
            pass

    # List of anniversaries
    for row in rows:
        if row['Marriage date'] and row['Gender'] == 'M':
            event = {}
            event['date'] = datetime.datetime.strptime(row['Marriage date'], "%b. %d %Y")
            event['reason'] = "Anniversary of %s %s and %s (married in %s)" % (row['First name'], row['Last name'], row['Marriage to'], event['date'].year)
            special_days.append(event)

    # Group by Month:
    events_by_month = collections.defaultdict(list)
    for event in special_days:
        events_by_month[event['date'].month].append(event)

    # Sort each month:
    for month_num in events_by_month.keys():
        events_by_month[month_num] = sorted(events_by_month[month_num], key=lambda i:(i['date'].day, i['reason']))
    
    return events_by_month
        
def generate_pdf(events_by_month, output):
    styles = reportlab.lib.styles.getSampleStyleSheet()
    style = styles["Normal"]
    style_title = styles["Title"]

    story = []

    p = reportlab.platypus.Paragraph("<b>Family Birthdays and Anniversaries</b>", style_title)
    story.append(p)

    spacer = reportlab.platypus.KeepTogether(reportlab.platypus.Spacer(1,0.2*reportlab.lib.units.inch))

    first = True
    for month_num in events_by_month.keys():
        if first:
            first = False
        else:
            story.append(spacer)
        p = reportlab.platypus.Paragraph("<font size=12><b>%s</b></font>" % calendar.month_name[month_num], style)
        story.append(p)
        for event in events_by_month[month_num]:
            event_text = "%s %s" % (event['date'].day, event['reason'])
            p = reportlab.platypus.Paragraph(event_text, style)
            story.append(p)
       
    doc = reportlab.platypus.SimpleDocTemplate(output, pagesize=reportlab.lib.pagesizes.letter, title="Family Birthdays and Anniversaries")
    doc.build(story)
    
def main():
    parser = argparse.ArgumentParser(description="Script for converting FamilyTreeBuilder CSV output into a PDF")
    parser.add_argument('-i', '--input', required=True, help='FamilyTreeBuilder CSV to transform')
    parser.add_argument('-o', '--output', required=True, help='Destination file for output')
    args = parser.parse_args()

    events_by_month = parse_input(args.input)

    generate_pdf(events_by_month, args.output)
    
if __name__ == "__main__":
    main()
