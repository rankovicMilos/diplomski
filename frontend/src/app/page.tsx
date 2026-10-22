import { Suspense } from "react";
import LatestMarketPositions from "../components/Analysis/LatestMarketPositions/LatestMarketPositions";
import SearchByClient from "../components/Analysis/LatestMarketPositions/SearchByClient";


const HomePage = () => {


  return (
    <div className="pa-3 pr-6 flex flex-col gap-4">
      <div className="flex justify-between items-center flex-wrap gap-y-4">
        <h1>Analysis Documents</h1>
        <Suspense>
          <SearchByClient />
        </Suspense>
      </div>
      <Suspense>
        <LatestMarketPositions />
      </Suspense>

    </div>
  )
}

export default HomePage;