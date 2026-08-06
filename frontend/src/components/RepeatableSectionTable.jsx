/**
 * A small, dependency-free repeatable-row editor used for every
 * structured Daily Log section (Observed Weather Conditions, Manpower,
 * Equipment, Delivery, Inspection, HSE, Visitors). One reusable table
 * instead of seven near-identical bespoke forms - adding a new log
 * section later means adding a columns array, not a new component.
 */
export function emptyRow(columns) {
  const row = {};
  columns.forEach((col) => {
    row[col.key] = col.type === "checkbox" ? false : "";
  });
  return row;
}

function RepeatableSectionTable({ columns, rows, onChange, addLabel = "+ Add row" }) {
  function updateCell(index, key, value) {
    const next = rows.map((row, i) => (i === index ? { ...row, [key]: value } : row));
    onChange(next);
  }

  function addRow() {
    onChange([...rows, emptyRow(columns)]);
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
              {columns.map((col) => (
                <th key={col.key}>{col.label}</th>
              ))}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.type === "checkbox" ? (
                      <input
                        type="checkbox"
                        checked={Boolean(row[col.key])}
                        onChange={(e) => updateCell(index, col.key, e.target.checked)}
                      />
                    ) : col.type === "select" ? (
                      <select
                        value={row[col.key] ?? ""}
                        onChange={(e) => updateCell(index, col.key, e.target.value)}
                      >
                        <option value="">--</option>
                        {col.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={col.type || "text"}
                        step={col.type === "number" ? "any" : undefined}
                        value={row[col.key] ?? ""}
                        placeholder={col.placeholder}
                        onChange={(e) => updateCell(index, col.key, e.target.value)}
                      />
                    )}
                  </td>
                ))}
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
        {addLabel}
      </button>
    </div>
  );
}

export default RepeatableSectionTable;
