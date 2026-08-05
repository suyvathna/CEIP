import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { createDailyLog, getDailyLog, updateDailyLog } from "../api/dailyLogs";
import { todayLocalISODate } from "../utils/date";
import RepeatableSectionTable from "../components/RepeatableSectionTable";
import RainRecordsTable from "../components/RainRecordsTable";

const HSE_CATEGORIES = [
  "Toolbox Talk", "Incident", "Near Miss", "PPE Violation",
  "Housekeeping", "Inspection", "Other",
];

const SNAPSHOT_TIMES = [
  "06:00 AM", "09:00 AM", "12:00 PM", "03:00 PM", "06:00 PM", "09:00 PM",
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

function emptySnapshot() {
  return SNAPSHOT_TIMES.map((time) => ({ time, condition: "", temp_c: "" }));
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
  const [snapshot, setSnapshot] = useState(emptySnapshot());
  const [weatherObservations, setWeatherObservations] = useState([]);
  const [manpowerEntries, setManpowerEntries] = useState([]);
  const [equipmentEntries, setEquipmentEntries] = useState([]);
  const [deliveryEntries, setDeliveryEntries] = useState([]);
  const [inspectionEntries, setInspectionEntries] = useState([]);
  const [hseEntries, setHseEntries] = useState([]);
  const [visitorEntries, setVisitorEntries] = useState([]);

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
        setSnapshot(
          data.daily_snapshot?.length ? data.daily_snapshot : emptySnapshot()
        );
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

  function updateSnapshotSlot(index, key, value) {
    setSnapshot(snapshot.map((slot, i) => (i === index ? { ...slot, [key]: value } : slot)));
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
      daily_snapshot: snapshot
        .filter((s) => s.condition || s.temp_c !== "")
        .map((s) => ({ ...s, temp_c: numOrNull(s.temp_c) })),
      weather_observations: cleanRows(weatherObservations),
      manpower_entries: cleanRows(manpowerEntries, ["workers_count", "hours"]),
      equipment_entries: cleanRows(equipmentEntries, ["hours_operating", "hours_idle"]),
      delivery_entries: cleanRows(deliveryEntries),
      inspection_entries: cleanRows(inspectionEntries),
      hse_entries: cleanRows(hseEntries),
      visitor_entries: cleanRows(visitorEntries),
    };

    try {
      if (isEdit) {
        await updateDailyLog(dailyLogId, payload);
        navigate(`/projects/${projectId}/daily-log/${dailyLogId}`);
      } else {
        const created = await createDailyLog(payload);
        navigate(`/projects/${projectId}/daily-log/${created.id}`);
      }
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  if (loading) return <p>Loading Daily Log...</p>;

  return (
    <div className="new-daily-log-page legacy-page">
      <Link to={`/projects/${projectId}`}>&larr; Back to project</Link>
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

        <h2>Daily Snapshot</h2>
        <table className="repeatable-table">
          <thead>
            <tr>
              {SNAPSHOT_TIMES.map((t) => <th key={t}>{t}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr>
              {snapshot.map((slot, i) => (
                <td key={slot.time}>
                  <input
                    type="text"
                    placeholder="Condition"
                    value={slot.condition}
                    onChange={(e) => updateSnapshotSlot(i, "condition", e.target.value)}
                  />
                  <input
                    type="number"
                    step="any"
                    placeholder="°C"
                    value={slot.temp_c}
                    onChange={(e) => updateSnapshotSlot(i, "temp_c", e.target.value)}
                  />
                </td>
              ))}
            </tr>
          </tbody>
        </table>

        <h2>Rain Records</h2>
        <RainRecordsTable
          dailyLogId={isEdit ? dailyLogId : null}
          rows={weatherObservations}
          onChange={setWeatherObservations}
        />
        {!isEdit && (
          <p className="form-hint">
            Photos can be attached to a rain record once this entry is
            saved.
          </p>
        )}

        <h2>Notes</h2>
        <label>
          Work completed / site activity today
          <textarea name="work_completed" value={flat.work_completed} onChange={handleFlatChange} />
        </label>
        <label>
          Delays
          <textarea name="delays" value={flat.delays} onChange={handleFlatChange} />
        </label>
        <label>
          Engineer instruction
          <textarea name="engineer_instruction" value={flat.engineer_instruction} onChange={handleFlatChange} />
        </label>
        <label>
          Plan for tomorrow
          <textarea name="tomorrow_plan" value={flat.tomorrow_plan} onChange={handleFlatChange} />
        </label>
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

        <p className="form-hint">
          Photos can be added from the Daily Log page once this entry is
          saved.
        </p>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : isEdit ? "Save changes" : "Save Daily Log"}
        </button>
      </form>
    </div>
  );
}

export default NewDailyLogPage;
