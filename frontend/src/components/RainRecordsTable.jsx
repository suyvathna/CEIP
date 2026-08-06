import { useState } from "react";
import { uploadEvidence } from "../api/evidence";
import { BASE_URL } from "../api/client";

/**
 * "Rain Records" - the one Daily Log section with a real per-row photo
 * upload, which is why it isn't just another RepeatableSectionTable
 * columns array: the Photo cell needs to call the Evidence API and knows
 * about dailyLogId, neither of which the generic table needs to know
 * about for its other six sections.
 *
 * Photo upload only works once the Daily Log itself has an id (Evidence
 * rows are owned by daily_log_id) - same "save first" constraint the
 * day's own Photos section already has.
 */
// evidence_id is "" (not null) until a photo is uploaded, matching the
// same empty-string convention every other field uses - cleanRows (see
// NewDailyLogPage.jsx) treats "" as "unset" when deciding whether a row
// is blank enough to drop, but not null, so a null default here would
// make an otherwise-empty row always survive that filter.
export function emptyRow() {
  return { start_time: "", end_time: "", caused_delay: false, evidence_id: "", comments: "" };
}

function PhotoCell({ dailyLogId, row, onChange }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const evidence = await uploadEvidence({ dailyLogId }, file, { category: "Rain" });
      onChange({ ...row, evidence_id: evidence.id });
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  if (!dailyLogId) {
    return <span className="form-hint">Save log first</span>;
  }

  if (row.evidence_id) {
    return (
      <div>
        <a href={`${BASE_URL}/evidence/download/${row.evidence_id}`} target="_blank" rel="noreferrer">
          <img
            src={`${BASE_URL}/evidence/download/${row.evidence_id}`}
            alt="Rain record"
            style={{ width: 60, height: 60, objectFit: "cover", borderRadius: 4, display: "block" }}
          />
        </a>
        <button type="button" onClick={() => onChange({ ...row, evidence_id: "" })}>
          Remove
        </button>
      </div>
    );
  }

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFile} disabled={uploading} />
      {uploading && <span className="form-hint">Uploading...</span>}
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}

function RainRecordsTable({ dailyLogId, rows, onChange }) {
  function updateRow(index, next) {
    onChange(rows.map((row, i) => (i === index ? next : row)));
  }

  function addRow() {
    onChange([...rows, emptyRow()]);
  }

  function removeRow(index) {
    onChange(rows.filter((_, i) => i !== index));
  }

  return (
    <div className="repeatable-table-wrapper">
      {rows.length > 0 && (
        <table className="repeatable-table">
          <thead>
            <tr>
              <th>Start time</th>
              <th>Finish time</th>
              <th>Caused delay?</th>
              <th>Photo</th>
              <th>Comments</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>
                <td>
                  <input
                    type="time"
                    value={row.start_time || ""}
                    onChange={(e) => updateRow(index, { ...row, start_time: e.target.value })}
                  />
                </td>
                <td>
                  <input
                    type="time"
                    value={row.end_time || ""}
                    onChange={(e) => updateRow(index, { ...row, end_time: e.target.value })}
                  />
                </td>
                <td>
                  <input
                    type="checkbox"
                    checked={Boolean(row.caused_delay)}
                    onChange={(e) => updateRow(index, { ...row, caused_delay: e.target.checked })}
                  />
                </td>
                <td>
                  <PhotoCell
                    dailyLogId={dailyLogId}
                    row={row}
                    onChange={(next) => updateRow(index, next)}
                  />
                </td>
                <td>
                  <input
                    type="text"
                    value={row.comments || ""}
                    onChange={(e) => updateRow(index, { ...row, comments: e.target.value })}
                  />
                </td>
                <td>
                  <button
                    type="button"
                    className="repeatable-remove-row"
                    onClick={() => removeRow(index)}
                    aria-label="Remove row"
                  >
                    &times;
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <button type="button" className="repeatable-add-row" onClick={addRow}>
        + Add rain record
      </button>
    </div>
  );
}

export default RainRecordsTable;
