function getItemImageUrl(item) {
  if (!item?.icon_url) return null;
  return `https://community.cloudflare.steamstatic.com/economy/image/${item.icon_url}/180fx180f`;
}

function getTagValue(tags, category) {
  return tags?.find((tag) => tag.category === category)?.localized_tag_name ?? "—";
}

function InventoryGrid({ items = [] }) {
  if (!items.length) {
    return (
      <div className="content-card">
        <h3>Inventário Steam</h3>
        <p>Nenhum item encontrado.</p>
      </div>
    );
  }

  return (
    <div className="content-card">
      <h3>Inventário Steam</h3>

      <div className="inventory-grid">
        {items.map((item) => {
          const imageUrl = getItemImageUrl(item);
          const rarity = getTagValue(item.tags, "Rarity");
          const exterior = getTagValue(item.tags, "Exterior");

          return (
            <article key={item.assetid} className="inventory-card">
              <div className="inventory-image-wrapper">
                {imageUrl ? (
                  <img
                    src={imageUrl}
                    alt={item.market_hash_name || item.name}
                    className="inventory-image"
                  />
                ) : (
                  <div className="inventory-image-placeholder">Sem imagem</div>
                )}
              </div>

              <div className="inventory-body">
                <h4>{item.market_hash_name || item.name}</h4>
                <p className="inventory-type">{item.type || "Sem tipo"}</p>

                <div className="inventory-meta">
                  <span>Raridade: {rarity}</span>
                  <span>Exterior: {exterior}</span>
                  <span>Tradable: {item.tradable ? "Sim" : "Não"}</span>
                  <span>Marketable: {item.marketable ? "Sim" : "Não"}</span>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

export default InventoryGrid;