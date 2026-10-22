import AnalysisSkeleton from "@/src/components/Analysis/Analysis.loading";
import ClientPosition from "@/src/components/Analysis/ClientPosition/ClientPosition";
import { Suspense } from "react";

const ClientPositionPage = () => {

  return (
    <Suspense fallback={<AnalysisSkeleton />}>
      <ClientPosition />
    </Suspense>
  )
}

export default ClientPositionPage;
