function getItemImageUrl(item) {
  if (!item?.icon_url) return null;
  return `https://community.cloudflare.steamstatic.com/economy/image/${item.icon_url}/180fx180f`;
}

function getTag(tags, category) {
  return tags?.find((tag) => tag.category === category) ?? null;
}

// Fallback rarity → colour map (Steam usually ships a `color` on the tag,
// but we cover the common CS rarities by name just in case).
const RARITY_FALLBACK = {
  "consumer grade": "b0c3d9",
  "industrial grade": "5e98d9",
  "mil-spec grade": "4b69ff",
  "restricted": "8847ff",
  "classified": "d32ce6",
  "covert": "eb4b4b",
  "contraband": "e4ae39",
  "extraordinary": "eb4b4b",
};

function getRarity(tags) {
  const tag = getTag(tags, "Rarity");
  if (!tag) return { label: "—", color: "94a3b8" };
  const name = tag.localized_tag_name || "—";
  const color = tag.color || RARITY_FALLBACK[name.toLowerCase()] || "94a3b8";
  return { label: name, color };
}

function PriceChange({ change }) {
  if (!change) {
    return (
      <div className="mt-auto flex items-baseline justify-between pt-1">
        <span className="text-sm text-slate-600">Sem dados de preço</span>
      </div>
    );
  }

  const pct = change.change_pct ?? 0;
  const up = pct > 0;
  const flat = pct === 0;
  const color = flat ? "text-slate-400" : up ? "text-emerald-400" : "text-rose-400";
  const arrow = flat ? "→" : up ? "▲" : "▼";

  return (
    <div className="mt-auto flex items-baseline justify-between pt-1">
      <span className="text-base font-bold text-slate-100">
        ${change.current_price.toFixed(2)}
      </span>
      <span className={`text-xs font-semibold tabular-nums ${color}`}>
        {arrow} {up ? "+" : ""}{pct.toFixed(1)}%
      </span>
    </div>
  );
}

function InventoryGrid({ items = [], priceChanges = {} }) {
  if (!items.length) {
    return (
      <div className="border border-slate-800 bg-[#17191A] p-10 text-center text-sm text-slate-500">
        Nenhum item encontrado no inventário.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {items.map((item) => {
        const imageUrl = getItemImageUrl(item);
        const rarity = getRarity(item.tags);
        const exterior = getTag(item.tags, "Exterior")?.localized_tag_name ?? "—";
        const accent = `#${rarity.color}`;
        const change = priceChanges[item.market_hash_name] || null;

        return (
          <article
            key={item.assetid}
            className="group relative flex flex-col overflow-hidden border border-slate-800 bg-[#17191A] transition-all hover:-translate-y-1 hover:border-slate-600"
            style={{ boxShadow: `inset 0 -3px 0 0 ${accent}` }}
          >
            {/* rarity glow on hover */}
            <div
              className="pointer-events-none absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100"
              style={{ background: `radial-gradient(120% 80% at 50% 0%, ${accent}22, transparent 70%)` }}
            />

            <div className="relative flex h-32 items-center justify-center bg-[#0f1011] p-3">
              {imageUrl ? (
                <img
                  src={imageUrl}
                  alt={item.market_hash_name || item.name}
                  className="max-h-full max-w-full object-contain transition-transform group-hover:scale-110"
                />
              ) : (
                <span className="text-xs text-slate-600">Sem imagem</span>
              )}
            </div>

            <div className="relative flex flex-1 flex-col gap-2 p-3">
              <h4 className="line-clamp-2 text-sm font-semibold text-slate-100" title={item.market_hash_name || item.name}>
                {item.market_hash_name || item.name}
              </h4>

              <span
                className="w-fit px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest"
                style={{ color: accent, border: `1px solid ${accent}66`, background: `${accent}14` }}
              >
                {rarity.label}
              </span>

              <div className="flex flex-wrap gap-1.5 pt-1 text-[10px] uppercase tracking-wider text-slate-500">
                <span className="border border-slate-700/70 px-1.5 py-0.5">{exterior}</span>
                {item.tradable && (
                  <span className="border border-emerald-700/40 px-1.5 py-0.5 text-emerald-400">Tradable</span>
                )}
                {item.marketable && (
                  <span className="border border-sky-700/40 px-1.5 py-0.5 text-sky-400">Marketable</span>
                )}
              </div>

              <div className="mt-auto border-t border-slate-800 pt-2">
                <PriceChange change={change} />
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}

export default InventoryGrid;
