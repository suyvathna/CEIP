import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import Button from "@mui/material/Button";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { createDailyLog, getDailyLog, updateDailyLog } from "../api/dailyLogs";
import { uploadEvidence } from "../api/evidence";
import { todayLocalISODate } from "../utils/date";
import RepeatableSectionTable, { emptyRow as emptySectionRow } from "../components/RepeatableSectionTable";
import RainRecordsTable, { emptyRow as emptyRainRow } from "../components/RainRecordsTable";
import StagedAttachments from "../components/StagedAttachments";

const HSE_CATEGORIES = [
  "Toolbox Talk", "Incident", "Near Miss", "PPE Violation",
  "Housekeeping", "Inspection", "Other",
];

const MANPOWER_COLUMNS = [
  { key: "company", label: "Company", type: "text" },
  { key: "trade", label: "Trade", type: "text" },
  { key: "position", label: "Position", type: "text" },
  { key: "workers_count", label: "Workers #", type: "number" },
  { key: "hours", label: "Hours", type: "number" },
  { key: "comments", label: "Comments", type: "text" },
];

const EQUIPMENT_COLUMNS = [
  { key: "equipment_name", label: "Equipment", type: "text" },
  { key: "equipment_type", label: "Type", type: "text" },
  { key: "hours_operating", label: "Hrs operating", type: "number" },
  { key: "hours_idle", label: "Hrs idle", type: "number" },
  { key: "inspected", label: "Inspected?", type: "checkbox" },
  { key: "inspection_time", label: "Inspection time", type: "time" },
  { key: "location", label: "Location", type: "text" },
  { key: "comments", label: "Comments", type: "text" },
];

const DELIVERY_COLUMNS = [
  { key: "delivery_time", label: "Time", type: "time" },
  { key: "delivered_from", label: "Delivered from", type: "text" },
  { key: "tracking_number", label: "Tracking #", type: "text" },
  { key: "contents", label: "Contents", type: "text" },
  { key: "comments", label: "Comments", type: "text" },
];

const INSPECTION_COLUMNS = [
  { key: "start_time", label: "Start time", type: "time" },
  { key: "end_time", label: "End time", type: "time" },
  { key: "inspection_type", label: "Inspection type", type: "text" },
  { key: "inspecting_entity", label: "Inspecting entity", type: "text" },
  { key: "inspector_name", label: "Inspector name", type: "text" },
  { key: "location_area", label: "Location/area", type: "text" },
  { key: "comments", label: "Comments", type: "text" },
];

const HSE_COLUMNS = [
  { key: "entry_time", label: "Time", type: "time" },
  { key: "category", label: "Category", type: "select", options: HSE_CATEGORIES },
  { key: "description", label: "Description", type: "text" },
  { key: "action_taken", label: "Action taken", type: "text" },
  { key: "reported_by", label: "Reported by", type: "text" },
];

const VISITOR_COLUMNS = [
  { key: "time_in", label: "Time in", type: "time" },
  { key: "time_out", label: "Time out", type: "time" },
  { key: "visitor_name", label: "Visitor name", type: "text" },
  { key: "company", label: "Company", type: "text" },
  { key: "purpose", label: "Purpose", type: "text" },
  { key: "host_name", label: "Hosted by", type: "text" },
];

function emptyFlatState() {
  return {
    diary_date: todayLocalISODate(),
    temp_avg_c: "", humidity_avg_pct: "",
    work_completed: "",
    delays: "",
    engineer_instruction: "",
    tomorrow_plan: "",
    remarks: "",
    manpower_notes: "",
    equipment_notes: "",
    materials_notes: "",
    hse_notes: "",
    visitor_notes: "",
  };
}

function numOrNull(v) {
  if (v === "" || v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

function cleanRows(rows, numericKeys = []) {
  // Drop fully-empty rows and coerce numeric fields, so a half-typed row
  // left over from clicking "+ Add row" doesn't get submitted as blanks.
  return rows
    .filter((row) => Object.values(row).some((v) => v !== "" && v !== false))
    .map((row) => {
      const cleaned = { ...row };
      numericKeys.forEach((k) => {
        if (k in cleaned) cleaned[k] = numOrNull(cleaned[k]);
      });
      Object.keys(cleaned).forEach((k) => {
        if (cleaned[k] === "") cleaned[k] = null;
      });
      return cleaned;
    });
}

function NewDailyLogPage() {
  const { projectId, eventId, dailyLogId } = useParams();
  const isEdit = Boolean(dailyLogId);

  const [flat, setFlat] = useState(emptyFlatState());
  const [weatherObservations, setWeatherObservations] = useState(isEdit ? [] : [emptyRainRow()]);
  const [manpowerEntries, setManpowerEntries] = useState(isEdit ? [] : [emptySectionRow(MANPOWER_COLUMNS)]);
  const [equipmentEntries, setEquipmentEntries] = useState(isEdit ? [] : [emptySectionRow(EQUIPMENT_COLUMNS)]);
  const [deliveryEntries, setDeliveryEntries] = useState(isEdit ? [] : [emptySectionRow(DELIVERY_COLUMNS)]);
  const [inspectionEntries, setInspectionEntries] = useState(isEdit ? [] : [emptySectionRow(INSPECTION_COLUMNS)]);
  const [hseEntries, setHseEntries] = useState(isEdit ? [] : [emptySectionRow(HSE_COLUMNS)]);
  const [visitorEntries, setVisitorEntries] = useState(isEdit ? [] : [emptySectionRow(VISITOR_COLUMNS)]);
  const [photos, setPhotos] = useState([]);

  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isEdit) return;
    getDailyLog(dailyLogId)
      .then((data) => {
        setFlat({
          diary_date: data.diary_date,
          temp_avg_c: data.temp_avg_c ?? "", humidity_avg_pct: data.humidity_avg_pct ?? "",
          work_completed: data.work_completed ?? "",
          delays: data.delays ?? "",
          engineer_instruction: data.engineer_instruction ?? "",
          tomorrow_plan: data.tomorrow_plan ?? "",
          remarks: data.remarks ?? "",
          manpower_notes: data.manpower_notes ?? "",
          equipment_notes: data.equipment_notes ?? "",
          materials_notes: data.materials_notes ?? "",
          hse_notes: data.hse_notes ?? "",
          visitor_notes: data.visitor_notes ?? "",
        });
        // evidence_id comes back as null (not "") for a row with no photo -
        // normalize it to "" so cleanRows' "is this row blank?" check
        // (which treats "" as unset but not null) works the same way for
        // rows loaded from the server as for freshly-added ones.
        setWeatherObservations(
          (data.weather_observations || []).map((row) => ({
            ...row,
            evidence_id: row.evidence_id ?? "",
          }))
        );
        setManpowerEntries(data.manpower_entries || []);
        setEquipmentEntries(data.equipment_entries || []);
        setDeliveryEntries(data.delivery_entries || []);
        setInspectionEntries(data.inspection_entries || []);
        setHseEntries(data.hse_entries || []);
        setVisitorEntries(data.visitor_entries || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [isEdit, dailyLogId]);

  function handleFlatChange(e) {
    setFlat({ ...flat, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      ...flat,
      project_id: projectId,
      event_id: eventId || null,
      temp_avg_c: numOrNull(flat.temp_avg_c),
      humidity_avg_pct: numOrNull(flat.humidity_avg_pct),
      weather_observations: cleanRows(weatherObservations),
      manpower_entries: cleanRows(manpowerEntries, ["workers_count", "hours"]),
      equipment_entries: cleanRows(equipmentEntries, ["hours_operating", "hours_idle"]),
      delivery_entries: cleanRows(deliveryEntries),
      inspection_entries: cleanRows(inspectionEntries),
      hse_entries: cleanRows(hseEntries),
      visitor_entries: cleanRows(visitorEntries),
    };

    try {
      let savedId = dailyLogId;
      if (isEdit) {
        await updateDailyLog(dailyLogId, payload);
      } else {
        savedId = (await createDailyLog(payload)).id;
      }

      for (const staged of photos) {
        await uploadEvidence(
          { dailyLogId: savedId },
          staged.file,
          { caption: staged.caption }
        );
      }

      navigate(`/projects/${projectId}/daily-log/${savedId}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  if (loading) return <p>Loading Daily Log...</p>;

  return (
    <div className="new-daily-log-page legacy-page">
      <Button
        component={Link}
        to={`/projects/${projectId}/report`}
        size="small"
        startIcon={<ArrowBackIcon fontSize="small" />}
        sx={{ alignSelf: "flex-start" }}
      >
        Back to Site Records
      </Button>
      <h1>{isEdit ? "Edit Daily Log" : "New Daily Log"}</h1>
      <p className="form-hint">
        Any event logged for this project on the same date links to this
        Daily Log entry automatically - no need to attach it by hand.
      </p>
      <form onSubmit={handleSubmit}>
        <label>
          Log date
          <input type="date" name="diary_date" value={flat.diary_date} onChange={handleFlatChange} required />
        </label>

        <h2>Weather Report</h2>
        <div className="field-grid">
          <label>Temp avg (°C)<input type="number" step="any" name="temp_avg_c" value={flat.temp_avg_c} onChange={handleFlatChange} /></label>
          <label>Humidity avg (%)<input type="number" step="any" name="humidity_avg_pct" value={flat.humidity_avg_pct} onChange={handleFlatChange} /></label>
        </div>
        <p className="form-hint">
          Filled in by hand for now - a future update can auto-fill this
          from a Phnom Penh weather feed.
        </p>

        <h2>Rain Records</h2>
        <RainRecordsTable
          dailyLogId={isEdit ? dailyLogId : null}
          rows={weatherObservations}
          onChange={setWeatherObservations}
        />

        <h2>Work completed / site activity today</h2>
        <textarea name="work_completed" value={flat.work_completed} onChange={handleFlatChange} />

        <h2>Delays</h2>
        <textarea name="delays" value={flat.delays} onChange={handleFlatChange} />

        <h2>Engineer instruction</h2>
        <textarea name="engineer_instruction" value={flat.engineer_instruction} onChange={handleFlatChange} />

        <h2>Plan for tomorrow</h2>
        <textarea name="tomorrow_plan" value={flat.tomorrow_plan} onChange={handleFlatChange} />

        <label>
          Remarks
          <textarea name="remarks" value={flat.remarks} onChange={handleFlatChange} />
        </label>

        <h2>Manpower Log</h2>
        <RepeatableSectionTable
          columns={MANPOWER_COLUMNS}
          rows={manpowerEntries}
          onChange={setManpowerEntries}
          addLabel="+ Add manpower row"
        />
        <label>
          Manpower notes
          <textarea name="manpower_notes" value={flat.manpower_notes} onChange={handleFlatChange} placeholder="Anything that doesn't fit a row above" />
        </label>

        <h2>Equipment Log</h2>
        <RepeatableSectionTable
          columns={EQUIPMENT_COLUMNS}
          rows={equipmentEntries}
          onChange={setEquipmentEntries}
          addLabel="+ Add equipment row"
        />
        <label>
          Equipment notes
          <textarea name="equipment_notes" value={flat.equipment_notes} onChange={handleFlatChange} />
        </label>

        <h2>Delivery Log</h2>
        <RepeatableSectionTable
          columns={DELIVERY_COLUMNS}
          rows={deliveryEntries}
          onChange={setDeliveryEntries}
          addLabel="+ Add delivery row"
        />
        <label>
          Materials notes
          <textarea name="materials_notes" value={flat.materials_notes} onChange={handleFlatChange} />
        </label>

        <h2>Inspection Log</h2>
        <RepeatableSectionTable
          columns={INSPECTION_COLUMNS}
          rows={inspectionEntries}
          onChange={setInspectionEntries}
          addLabel="+ Add inspection row"
        />

        <h2>HSE</h2>
        <RepeatableSectionTable
          columns={HSE_COLUMNS}
          rows={hseEntries}
          onChange={setHseEntries}
          addLabel="+ Add HSE entry"
        />
        <label>
          HSE notes
          <textarea name="hse_notes" value={flat.hse_notes} onChange={handleFlatChange} />
        </label>

        <h2>Visitors</h2>
        <RepeatableSectionTable
          columns={VISITOR_COLUMNS}
          rows={visitorEntries}
          onChange={setVisitorEntries}
          addLabel="+ Add visitor"
        />
        <label>
          Visitor notes
          <textarea name="visitor_notes" value={flat.visitor_notes} onChange={handleFlatChange} />
        </label>

        <h2>Photos</h2>
        <StagedAttachments items={photos} onChange={setPhotos} showCaption addLabel="+ Add photo" />

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : isEdit ? "Save changes" : "Save Daily Log"}
        </button>
      </form>
    </div>
  );
}

export default NewDailyLogPage;
