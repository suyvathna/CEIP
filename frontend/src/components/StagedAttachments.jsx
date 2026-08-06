import { useRef } from "react";

let nextStagedId = 0;

function toStagedFile(file) {
  nextStagedId += 1;
  return { id: nextStagedId, file, category: "General", caption: "" };
}

/**
 * Multi-file picker for "attach these while creating the record" flows
 * (New Event / New Daily Log Photos, New Correspondence reference docs).
 * Files just sit in local state here - the caller uploads them (via
 * uploadEvidence) once the parent record exists and has an id, then
 * discards this list. Pass `categories` (see constants/photoCategories.js)
 * to show a per-file Section dropdown + caption field; omit it for a
 * plain filename + remove list.
 */
function StagedAttachments({ items, onChange, categories, addLabel = "+ Add file" }) {
  const inputRef = useRef(null);

  function handleFilesSelected(e) {
    const chosen = Array.from(e.target.files || []);
    e.target.value = "";
    if (chosen.length === 0) return;
    onChange([...items, ...chosen.map(toStagedFile)]);
  }

  function updateItem(id, patch) {
    onChange(items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function removeItem(id) {
    onChange(items.filter((item) => item.id !== id));
  }

  return (
    <div className="repeatable-table-wrapper">
      {items.length > 0 && (
        <table className="repeatable-table">
          <thead>
            <tr>
              <th>File</th>
              {categories && <th>Section</th>}
              {categories && <th>Caption</th>}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.file.name}</td>
                {categories && (
                  <td>
                    <select
                      value={item.category}
                      onChange={(e) => updateItem(item.id, { category: e.target.value })}
                    >
                      {categories.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </td>
                )}
                {categories && (
                  <td>
                    <input
                      type="text"
                      value={item.caption}
                      onChange={(e) => updateItem(item.id, { caption: e.target.value })}
                      placeholder="e.g. V6 props (support) installation"
                    />
                  </td>
                )}
                <td>
                  <button
                    type="button"
                    className="repeatable-remove-row"
                    onClick={() => removeItem(item.id)}
                    aria-label="Remove file"
                  >
                    &times;
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <button type="button" className="repeatable-add-row" onClick={() => inputRef.current?.click()}>
        {addLabel}
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*,application/pdf"
        style={{ display: "none" }}
        onChange={handleFilesSelected}
      />
    </div>
  );
}

export default StagedAttachments;
