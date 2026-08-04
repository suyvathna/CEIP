from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.storage_service import download_file


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
            f"Daily Logs: {report['total_daily_logs']}",
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
                ["Claim No.", claim.claim_no or "—"],
                ["Governing clause", claim.governing_clause or "—"],
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
                ["Contractor's claimed cost", claim.claimed_cost_amount if claim.claimed_cost_amount is not None else "—"],
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
    response_rows = [["Date", "Type", "Days granted", "Cost awarded", "Comment"]]
    for response in data["responses"]:
        response_rows.append(
            [
                response.response_date,
                response.response_type,
                response.days_granted if response.days_granted is not None else "—",
                response.cost_awarded_amount if response.cost_awarded_amount is not None else "—",
                response.comment or "—",
            ]
        )
    if len(response_rows) == 1:
        response_rows.append(["No responses recorded yet.", "", "", "", ""])
    story.append(
        _styled_table(response_rows, col_widths=[3 * cm, 4 * cm, 2.5 * cm, 2.5 * cm, 4 * cm])
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


def _v(value, default="—"):
    return default if value is None or value == "" else value


def _fetch_thumbnail(evidence, max_width=5 * cm):
    """
    Best-effort inline photo thumbnail for the Photos section, matching
    the reference site-log template's per-photo layout. Evidence lives
    in MinIO, not the database, so this has to actually fetch bytes - if
    MinIO is unreachable, the object was removed, or the file isn't an
    image (e.g. a PDF delivery note attached as "evidence"), this quietly
    returns None and the caller falls back to filename/caption text only.
    A report generator should never 500 because one photo couldn't be
    fetched.
    """
    if not evidence.content_type or not evidence.content_type.startswith("image/"):
        return None

    try:
        response = download_file(evidence.object_name)
        data = response.read()
        response.close()
        response.release_conn()
        image = Image(BytesIO(data))
        if image.drawWidth > max_width:
            scale = max_width / image.drawWidth
            image.drawWidth *= scale
            image.drawHeight *= scale
        return image
    except Exception:
        return None


def _daily_log_flowables(report: dict, styles, embed_photos: bool = True) -> list:
    """
    One Daily Log's worth of flowables, in the same section order as the
    reference site-log template: Weather Report, Daily Snapshot,
    Observed Weather Conditions, Notes, Manpower/Equipment/Delivery/
    Inspection/HSE/Visitor logs, then Photos. Shared by both the
    single-day report and the project-wide compiled report so the two
    documents never drift into different layouts.
    """
    story = []

    heading = f"Daily Log: {report['diary_date']}"
    story.append(Paragraph(heading, styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("Weather Report", styles["Heading3"]))
    story.append(
        _styled_table(
            [
                ["Temp Low", "Temp High", "Temp Avg", "Precip. Since Midnight", "Humidity Avg", "Wind Avg"],
                [
                    _v(report.get("temp_low_c")),
                    _v(report.get("temp_high_c")),
                    _v(report.get("temp_avg_c")),
                    _v(report.get("precip_since_midnight_mm")),
                    _v(report.get("humidity_avg_pct")),
                    _v(report.get("wind_avg_kmh")),
                ],
            ],
            col_widths=[2.8 * cm] * 6,
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    snapshot = report.get("daily_snapshot") or []
    if snapshot:
        story.append(Paragraph("Daily Snapshot", styles["Heading3"]))
        slot_header = [slot.get("time", "") for slot in snapshot]
        slot_condition = [slot.get("condition", "") for slot in snapshot]
        slot_temp = [
            f"{slot['temp_c']}°C" if slot.get("temp_c") is not None else ""
            for slot in snapshot
        ]
        story.append(
            _styled_table(
                [slot_header, slot_condition, slot_temp],
                col_widths=[2.5 * cm] * len(snapshot),
            )
        )
        story.append(Spacer(1, 0.4 * cm))

    weather_obs = report.get("weather_observations") or []
    if weather_obs:
        story.append(Paragraph("Observed Weather Conditions", styles["Heading3"]))
        rows = [["Time", "Caused Delay?", "Sky", "Precipitation", "Wind", "Comments"]]
        for obs in weather_obs:
            rows.append(
                [
                    _v(obs.get("observed_time") if isinstance(obs, dict) else obs.observed_time),
                    "Yes" if (obs.get("caused_delay") if isinstance(obs, dict) else obs.caused_delay) else "No",
                    _v(obs.get("sky") if isinstance(obs, dict) else obs.sky),
                    _v(obs.get("precipitation") if isinstance(obs, dict) else obs.precipitation),
                    _v(obs.get("wind") if isinstance(obs, dict) else obs.wind),
                    _v(obs.get("comments") if isinstance(obs, dict) else obs.comments),
                ]
            )
        story.append(_styled_table(rows, col_widths=[2 * cm, 2.5 * cm, 2.5 * cm, 3 * cm, 2.5 * cm, 4 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    notes_fields = [
        ("Work completed", report.get("work_completed")),
        ("Delays", report.get("delays")),
        ("Engineer's instruction", report.get("engineer_instruction")),
        ("Tomorrow's plan", report.get("tomorrow_plan")),
        ("Remarks", report.get("remarks")),
    ]
    if any(value for _, value in notes_fields):
        story.append(Paragraph("Notes", styles["Heading3"]))
        for label, value in notes_fields:
            if value:
                story.append(Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

    manpower = report.get("manpower_entries") or []
    if manpower:
        total_workers = report.get("total_workers", 0)
        total_hours = report.get("total_man_hours", 0)
        story.append(
            Paragraph(
                f"Manpower Log &mdash; {total_workers} Workers | {total_hours} Man Hours",
                styles["Heading3"],
            )
        )
        rows = [["Company", "Trade", "Position", "Workers", "Hours", "Man Hours"]]
        for row in manpower:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            hours = get("hours") or 0
            workers = get("workers_count") or 0
            rows.append(
                [
                    _v(get("company")),
                    _v(get("trade")),
                    _v(get("position")),
                    workers,
                    hours,
                    round(float(hours) * workers, 1),
                ]
            )
        story.append(_styled_table(rows, col_widths=[4 * cm, 2.5 * cm, 3 * cm, 2 * cm, 2 * cm, 2.5 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    equipment = report.get("equipment_entries") or []
    if equipment:
        story.append(Paragraph("Equipment Log", styles["Heading3"]))
        rows = [["Equipment", "Type", "Hrs Operating", "Hrs Idle", "Inspected?", "Location"]]
        for row in equipment:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            rows.append(
                [
                    _v(get("equipment_name")),
                    _v(get("equipment_type")),
                    _v(get("hours_operating")),
                    _v(get("hours_idle")),
                    "Yes" if get("inspected") else "No",
                    _v(get("location")),
                ]
            )
        story.append(_styled_table(rows, col_widths=[3.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2 * cm, 3 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    delivery = report.get("delivery_entries") or []
    if delivery:
        story.append(Paragraph("Delivery Log", styles["Heading3"]))
        rows = [["Time", "Delivered From", "Tracking No.", "Contents"]]
        for row in delivery:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            rows.append(
                [
                    _v(get("delivery_time")),
                    _v(get("delivered_from")),
                    _v(get("tracking_number")),
                    _v(get("contents")),
                ]
            )
        story.append(_styled_table(rows, col_widths=[2 * cm, 4 * cm, 3 * cm, 7 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    inspection = report.get("inspection_entries") or []
    if inspection:
        story.append(Paragraph("Inspection Log", styles["Heading3"]))
        rows = [["Start", "End", "Type", "Entity", "Inspector", "Location"]]
        for row in inspection:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            rows.append(
                [
                    _v(get("start_time")),
                    _v(get("end_time")),
                    _v(get("inspection_type")),
                    _v(get("inspecting_entity")),
                    _v(get("inspector_name")),
                    _v(get("location_area")),
                ]
            )
        story.append(_styled_table(rows, col_widths=[2 * cm, 2 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    hse = report.get("hse_entries") or []
    if hse:
        story.append(Paragraph("HSE Log", styles["Heading3"]))
        rows = [["Time", "Category", "Description", "Action Taken", "Reported By"]]
        for row in hse:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            rows.append(
                [
                    _v(get("entry_time")),
                    _v(get("category")),
                    _v(get("description")),
                    _v(get("action_taken")),
                    _v(get("reported_by")),
                ]
            )
        story.append(_styled_table(rows, col_widths=[2 * cm, 2.5 * cm, 5 * cm, 4 * cm, 3 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    visitors = report.get("visitor_entries") or []
    if visitors:
        story.append(Paragraph("Visitor Log", styles["Heading3"]))
        rows = [["Time In", "Time Out", "Visitor", "Company", "Purpose", "Host"]]
        for row in visitors:
            get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
            rows.append(
                [
                    _v(get("time_in")),
                    _v(get("time_out")),
                    _v(get("visitor_name")),
                    _v(get("company")),
                    _v(get("purpose")),
                    _v(get("host_name")),
                ]
            )
        story.append(_styled_table(rows, col_widths=[2 * cm, 2 * cm, 3 * cm, 3.5 * cm, 4.5 * cm, 2.5 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    evidence = report.get("evidence") or []
    if evidence:
        story.append(Paragraph(f"Photos ({len(evidence)})", styles["Heading3"]))
        for item in evidence:
            thumbnail = _fetch_thumbnail(item) if embed_photos else None
            if thumbnail is not None:
                story.append(thumbnail)
            caption = item.caption or item.filename
            story.append(Paragraph(caption, styles["Normal"]))
            story.append(Spacer(1, 0.3 * cm))

    return story


def generate_daily_log_pdf(report: dict, project_name: str | None = None):
    """
    A single Daily Log, formatted to match the reference site-log
    template's section layout (Weather Report, Daily Snapshot, Observed
    Weather Conditions, Notes, the structured logs, then Photos) - the
    "similar format" PDF export requested for the Report tab, callable
    per-day from the Daily Log detail page.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    if project_name:
        story.append(Paragraph(project_name, styles["Title"]))
    story.extend(_daily_log_flowables(report, styles))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_project_daily_log_compilation_pdf(
    reports: list, project_name: str | None = None
):
    """
    Every Daily Log for a project (optionally date-range filtered - see
    daily_log_service.get_daily_reports_for_project), one after another,
    each formatted the same way generate_daily_log_pdf formats a single
    day. This is the Report tab's "compiled Daily Log record" export -
    the document a Contractor would actually hand an Engineer or DAAB as
    the day-by-day site record behind a claim.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Daily Log Compilation", styles["Title"]))
    if project_name:
        story.append(Paragraph(project_name, styles["Heading2"]))
    story.append(
        Paragraph(f"{len(reports)} day(s) included", styles["Normal"])
    )
    story.append(PageBreak())

    for index, report in enumerate(reports):
        story.extend(_daily_log_flowables(report, styles))
        if index < len(reports) - 1:
            story.append(PageBreak())

    if not reports:
        story.append(Paragraph("No Daily Log entries in this date range.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer