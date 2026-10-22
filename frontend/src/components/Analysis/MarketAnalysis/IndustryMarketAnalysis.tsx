'use client'
import { useQueryState } from 'nuqs';
import { getIndustryById } from '@/src/lib/industries';
import AnalysisError from '../Analysis.error';
import MarketAnalysis from './MarketAnalysis';
import IndustryOverview from './IndustryOverview';

const IndustryMarketAnalysis = () => {

  const [industryId] = useQueryState("industry", { defaultValue: "cereals" });
  const industry = getIndustryById(industryId);

  if (!industry) return <AnalysisError />

  const overview = <IndustryOverview industry={industry} />

  if (!industry.analysisCategory) return overview

  // TODO: only Electricity has its own UAF form for now
  if (industry.id === "electricity") return (
    <MarketAnalysis
      category={industry.analysisCategory}
      title={industry.name}
      newAnalysisHref="/analysis/new/electricity"
      fallback={overview}
    />
  )

  return <MarketAnalysis category={industry.analysisCategory} />
}

export default IndustryMarketAnalysis;
