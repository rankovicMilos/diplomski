import AnalysisSkeleton from '@/src/components/Analysis/Analysis.loading';
import IndustryMarketAnalysis from '@/src/components/Analysis/MarketAnalysis/IndustryMarketAnalysis';
import { Suspense } from 'react';

const MarketAnalysisPage = () => {

  return (
    <Suspense fallback={<AnalysisSkeleton />}>
      <IndustryMarketAnalysis />
    </Suspense>
  )
}

export default MarketAnalysisPage;
