export default function SkinTable({ skins }) {
  return (
    <div className="table-wrapper">
      <table className="skins-table">
        <thead>
          <tr>
            <th>Skin</th>
            <th>Source</th>
            <th>Currency</th>
            <th>Mean Price</th>
            <th>Quantity Sold</th>
          </tr>
        </thead>
        <tbody>
          {skins.map((skin, index) => (
            <tr key={`${skin.name}-${skin.source}-${index}`}>
              <td>{skin.name}</td>
              <td>{skin.source}</td>
              <td>{skin.currency}</td>
              <td>{Number(skin.mean_price).toFixed(2)}</td>
              <td>{skin.quantity_sold}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
