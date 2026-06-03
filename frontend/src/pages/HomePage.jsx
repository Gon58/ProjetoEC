import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ElectricBorder from "../components/ElectricBorder";
import SkinTable from "../components/SkinTable";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";

const banners = [
  { src: "/Banner1.png", alt: "Featured skin market banner 1" },
  { src: "/Banner2.png", alt: "Featured skin market banner 2" },
  { src: "/Banner3.png", alt: "Featured skin market banner 3" },
];

export default function HomePage() {
  const [activeBanner, setActiveBanner] = useState(0);
  const [skins, setSkins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const bannerActions = [
    () => navigate("/dashboard"),
    () => navigate("/chat"),
    () => navigate("/profile"),
  ];

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setActiveBanner((currentBanner) => (currentBanner + 1) % banners.length);
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    async function fetchSkins() {
      try {
        setLoading(true);
        const response = await axios.get(`${apiUrl}/skins?limit=30`);
        const sortedSkins = [...response.data].sort(
          (leftSkin, rightSkin) => Number(rightSkin.mean_price) - Number(leftSkin.mean_price)
        );
        setSkins(sortedSkins);
      } catch (fetchError) {
        setError("Unable to load skin data right now.");
        console.error("Error fetching homepage skins:", fetchError);
      } finally {
        setLoading(false);
      }
    }

    fetchSkins();
  }, []);

  function goToPreviousBanner() {
    setActiveBanner((currentBanner) =>
      (currentBanner - 1 + banners.length) % banners.length
    );
  }

  function goToNextBanner() {
    setActiveBanner((currentBanner) => (currentBanner + 1) % banners.length);
  }

  const hottestSkins = [...skins]
    .sort((leftSkin, rightSkin) => Number(rightSkin.quantity_sold) - Number(leftSkin.quantity_sold))
    .slice(0, 3);

  return (
    <section className="flex flex-col gap-20 pb-20 md:gap-24 md:pb-28">
      <div className="relative mx-auto w-full max-w-360 px-4 py-3 mt-8" aria-label="Featured banners">
        <div className="relative aspect-16/7 min-h-80 w-full overflow-hidden">
          {banners.map((banner, bannerIndex) => (
            <button
              key={banner.src}
              type="button"
              onClick={bannerActions[bannerIndex]}
              disabled={!bannerActions[bannerIndex]}
              className={`absolute cursor-pointer inset-0 transition-all duration-300 ease-out ${bannerIndex === activeBanner ? "pointer-events-auto opacity-100 scale-100" : "pointer-events-none opacity-0 scale-[0.985]"}`}
              aria-hidden={bannerIndex !== activeBanner}
            >
              <img
                src={banner.src}
                alt={banner.alt}
                className="h-full w-full object-cover border border-white/10 shadow-[0_18px_42px_rgba(0,0,0,0.35)] [clip-path:polygon(44px_0,100%_0,100%_calc(100%-44px),calc(100%-44px)_100%,0_100%,0_44px)]"
              />
            </button>
          ))}
        </div>

        <button
          type="button"
          className="absolute cursor-pointer left-6 top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-full border border-white/15 bg-slate-950/70 text-slate-50 shadow-lg backdrop-blur-md transition-colors hover:bg-slate-800/90"
          onClick={goToPreviousBanner}
          aria-label="Show previous banner"
        >
          ‹
        </button>

        <button
          type="button"
          className="absolute cursor-pointer right-6 top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-full border border-white/15 bg-slate-950/70 text-slate-50 shadow-lg backdrop-blur-md transition-colors hover:bg-slate-800/90"
          onClick={goToNextBanner}
          aria-label="Show next banner"
        >
          ›
        </button>

        <div
          className="absolute bottom-6 left-1/2 flex -translate-x-1/2 gap-2.5 rounded-full bg-slate-950/55 px-3.5 py-2.5 backdrop-blur-md"
          aria-label="Banner navigation"
        >
          {banners.map((banner, bannerIndex) => (
            <button
              key={banner.src}
              type="button"
              className={`h-2.5 w-2.5 rounded-full border-0 transition-colors ${bannerIndex === activeBanner ? "bg-slate-50" : "bg-slate-200/35"}`}
              onClick={() => setActiveBanner(bannerIndex)}
              aria-label={`Show banner ${bannerIndex + 1}`}
              aria-pressed={bannerIndex === activeBanner}
            />
          ))}
        </div>
      </div>

      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          What is hot?
        </h2>
        <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2 xl:grid-cols-3">
          {hottestSkins.map((skin) => (
            <ElectricBorder
              key={`${skin.name}-${skin.source}`}
              color="#7df9ff"
              speed={1}
              chaos={0.12}
              borderRadius={14}
              className="mx-auto w-full max-w-72"
            >
              <article className="flex aspect-2/3 w-full flex-col items-center justify-center rounded-xl bg-[#17191A] px-5 py-6 text-center">
                <h3 className="mb-2 text-base font-semibold text-slate-100">{skin.name}</h3>
                <p className="text-sm text-slate-300">Quantity Sold: {skin.quantity_sold}</p>
              </article>
            </ElectricBorder>
          ))}
        </div>
      </section>

      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Having doubts?
        </h2>

        <div className="flex flex-col items-center gap-4 md:flex-row md:justify-center md:gap-6">
          <div className="flex justify-center md:justify-end">
            <img
              src="/TeacherBotConnor.png"
              alt="Teacher Bot Connor"
              className="h-72 w-72 border border-sky-300/35 object-cover shadow-[0_0_30px_rgba(56,189,248,0.22)] md:h-80 md:w-80"
            />
          </div>

          <div className="max-w-xl text-center md:text-left">
            <p className="text-4xl font-black uppercase leading-none tracking-[0.08em] text-sky-100 md:text-6xl">
              <span className="block">Talk with</span>
              <span className="block text-cyan-200">
                Teacher Bot Connor
              </span>
            </p>
            <button
              type="button"
              className="mt-4 cursor-pointer border border-sky-200/40 bg-sky-400 px-7 py-3 uppercase font-semibold tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300"
              onClick={() => navigate("/chat")}
            >
              Go to Chat
            </button>
          </div>
        </div>
      </section>

      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Featured market data
        </h2>

        <div className="mt-8">
          {loading ? <p className="text-center text-slate-400">Loading skin data...</p> : null}
          {error ? <p className="logs-error text-center">{error}</p> : null}
          {!loading && !error ? <SkinTable skins={skins} /> : null}
        </div>

        <div className="mt-10 flex justify-center">
          <button
            type="button"
            className="cursor-pointer border border-sky-200/40 bg-sky-400 px-8 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300"
            onClick={() => navigate("/dashboard")}
          >
            See more
          </button>
        </div>
      </section>
    </section>
  );
}
