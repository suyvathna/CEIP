from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_project_report_pdf(report: dict):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>CEIP Project Report</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Project:</b> {report['project_name']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Events: {report['total_events']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Daily Diaries: {report['total_daily_diaries']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Evidence: {report['total_evidence']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Open Events: {report['open_events']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Closed Events: {report['closed_events']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"High Severity: {report['high_severity']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Medium Severity: {report['medium_severity']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Low Severity: {report['low_severity']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Latest Event: {report['latest_event']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Generated: {report['generated_at']}",
            styles["Normal"],
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


def _styled_table(rows, col_widths=None):
    """
    One consistent look for every table in the claim report: a shaded
    header row, thin grid lines, and small wrapped body text so a long
    fact description or comment doesn't just run off the page edge.
    """
    styles = getSampleStyleSheet()
    wrapped = [
        [Paragraph(str(cell), styles["Normal"]) for cell in row] for row in rows
    ]
    table = Table(wrapped, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def generate_claim_report_pdf(data: dict):
    """
    The document behind both the Contractor's own "download this claim"
    button and the no-account public share link (see
    claim_service.get_claim_report_data for how `data` is assembled).
    It is meant to stand on its own: everything a recipient needs to
    understand the claim's current state - the deadline clock, the
    fact-by-fact agreement register, the supporting events, and the
    response history - is in the document itself, with no requirement to
    log into anything to make sense of it.
    """
    claim = data["claim"]
    clock = data["clock"]
    fact_summary = data["fact_summary"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FIDIC Sub-Clause 20.2 Claim Report", styles["Title"]))
    if data.get("project_name"):
        story.append(Paragraph(data["project_name"], styles["Heading2"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(claim.title, styles["Heading2"]))
    if claim.description:
        story.append(Paragraph(claim.description, styles["Normal"]))
    story.append(Spacer(1, 0.2 * cm))

    story.append(
        _styled_table(
            [
                ["Field", "Value"],
                ["Status", claim.status],
                ["Claim type", claim.claim_type],
                ["Claiming party", claim.claiming_party],
                ["Awareness date", claim.awareness_date],
                ["Notice submitted", claim.notice_submitted_date or "Not yet submitted"],
                [
                    "Detailed claim submitted",
                    claim.detailed_claim_submitted_date or "Not yet submitted",
                ],
                ["Contractor's claimed days", claim.claimed_days if claim.claimed_days is not None else "—"],
            ],
            col_widths=[6 * cm, 10 * cm],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Deadline clock (Sub-Clause 20.2)", styles["Heading3"]))
    clock_rows = [["Stage", "Deadline", "Status", "Completed"]]
    for stage in clock["stages"]:
        clock_rows.append(
            [
                stage["label"],
                stage["deadline"],
                stage["status"].replace("_", " "),
                stage["completed_date"] or "—",
            ]
        )
    story.append(
        _styled_table(clock_rows, col_widths=[7 * cm, 3 * cm, 3 * cm, 3 * cm])
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Fact-agreement register", styles["Heading3"]))
    story.append(
        Paragraph(
            f"Agreed days: <b>{fact_summary['agreed_days_total']}</b> &nbsp;|&nbsp; "
            f"Disputed days: <b>{fact_summary['disputed_days_total']}</b> &nbsp;|&nbsp; "
            f"Contractor's ask: <b>{fact_summary['claimed_days'] if fact_summary['claimed_days'] is not None else '—'}</b> "
            f"&nbsp;|&nbsp; {fact_summary['agreed_facts']}/{fact_summary['total_facts']} facts agreed",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    fact_rows = [["Description", "Proposed by", "Status", "Days"]]
    for fact in data["facts"]:
        fact_rows.append(
            [
                fact.description,
                fact.proposed_by_party,
                fact.status,
                fact.agreed_days if fact.agreed_days is not None else "—",
            ]
        )
    if len(fact_rows) == 1:
        fact_rows.append(["No facts proposed yet.", "", "", ""])
    story.append(
        _styled_table(fact_rows, col_widths=[8 * cm, 3 * cm, 3 * cm, 2 * cm])
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Supporting events", styles["Heading3"]))
    event_rows = [["Date", "Title", "Type", "Severity"]]
    for event in data["events"]:
        event_rows.append(
            [event.event_date, event.title, event.event_type, event.severity]
        )
    if len(event_rows) == 1:
        event_rows.append(["No events linked.", "", "", ""])
    story.append(
        _styled_table(event_rows, col_widths=[3 * cm, 7 * cm, 3 * cm, 3 * cm])
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Response history", styles["Heading3"]))
    response_rows = [["Date", "Type", "Days granted", "Comment"]]
    for response in data["responses"]:
        response_rows.append(
            [
                response.response_date,
                response.response_type,
                response.days_granted if response.days_granted is not None else "—",
                response.comment or "—",
            ]
        )
    if len(response_rows) == 1:
        response_rows.append(["No responses recorded yet.", "", "", ""])
    story.append(
        _styled_table(response_rows, col_widths=[3 * cm, 4 * cm, 3 * cm, 6 * cm])
    )
    story.append(Spacer(1, 0.7 * cm))

    story.append(
        Paragraph(
            "Generated by CEIP from the Contractor's own records at the time "
            "of export. This report is provided for information; it is not "
            "itself a substitute for the underlying Notice of Claim, "
            "detailed particulars, or evidence referenced above.",
            styles["Italic"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer