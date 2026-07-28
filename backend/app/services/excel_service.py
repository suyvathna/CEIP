from io import BytesIO

from openpyxl import Workbook


def generate_project_report_excel(report: dict):
    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Project Report"

    sheet.append(["Item", "Value"])

    sheet.append(["Project Name", report["project_name"]])
    sheet.append(["Total Events", report["total_events"]])
    sheet.append(["Total Daily Diaries", report["total_daily_diaries"]])
    sheet.append(["Total Evidence", report["total_evidence"]])

    sheet.append(["Open Events", report["open_events"]])
    sheet.append(["Closed Events", report["closed_events"]])

    sheet.append(["High Severity", report["high_severity"]])
    sheet.append(["Medium Severity", report["medium_severity"]])
    sheet.append(["Low Severity", report["low_severity"]])

    sheet.append(["Latest Event", report["latest_event"]])

    sheet.append(["Generated At", str(report["generated_at"])])

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return output