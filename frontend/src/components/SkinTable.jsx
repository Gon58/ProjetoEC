export default function SkinTable({ skins }) {
  return (
    <div className="table-wrapper">
      <table className="skins-table">
        <thead>
          <tr>
            <th>Skin</th>
            <th>Weapon</th>
            <th>Rarity</th>
            <th>Price</th>
            <th>Popularity</th>
          </tr>
        </thead>
        <tbody>
          {skins.map((skin) => (
            <tr key={skin.id}>
              <td>{skin.name}</td>
              <td>{skin.weapon}</td>
              <td>{skin.rarity}</td>
              <td>€{skin.price.toFixed(2)}</td>
              <td>{skin.popularity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
