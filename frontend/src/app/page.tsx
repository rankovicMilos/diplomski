import { Suspense } from "react";
import LatestMarketPositions from "../components/Analysis/LatestMarketPositions/LatestMarketPositions";
import SearchByClient from "../components/Analysis/LatestMarketPositions/SearchByClient";


const HomePage = () => {


  return (
    <div className="flex flex-col gap-4">
      <div className="glass relative overflow-hidden rounded-md px-5 md:px-8 py-8 flex justify-between items-center flex-wrap gap-y-4">
        <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-teal-100/20 blur-3xl" />
        <div className="relative flex flex-col gap-2">
          <span className="text-2xs font-semibold uppercase tracking-[0.18em] text-teal-100">Analiza sektorskog rizika</span>
          <h1>Analitički dokumenti</h1>
          <p className="text-charcoal-80 max-w-[46ch]">Pregled izveštaja o tržišnoj poziciji klijenata, razvrstanih po NACE delatnosti.</p>
        </div>
        <div className="relative">
          <Suspense>
            <SearchByClient />
          </Suspense>
        </div>
      </div>
      <Suspense>
        <LatestMarketPositions />
      </Suspense>

    </div>
  )
}

export default HomePage;