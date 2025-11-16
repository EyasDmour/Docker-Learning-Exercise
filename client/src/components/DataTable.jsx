import PropTypes from "prop-types";

const renderCellValue = (value) => {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
};

export default function DataTable({ rows }) {
  if (!rows || rows.length === 0) {
    return null;
  }

  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));

  return (
    <table>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={index}>
            {columns.map((column) => (
              <td key={column}>{renderCellValue(row[column])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

DataTable.propTypes = {
  rows: PropTypes.arrayOf(PropTypes.object)
};
