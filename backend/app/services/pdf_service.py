from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate


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