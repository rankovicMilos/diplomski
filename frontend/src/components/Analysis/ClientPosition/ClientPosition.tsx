'use client'
import { useState } from 'react';
import { Button, Divider } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import AnalysisSkeleton from '../Analysis.loading';
import AnalysisError from '../Analysis.error';
import useClientPositionQuery from '@/src/hooks/queries/useClientPositionQuery';
import { useQueryState } from 'nuqs';
import MarketPosition from './MarketPosition/MarketPosition';
import PeerAnalysis from './PeerAnalysis/PeerAnalysis';
import generateClientPositionDocx from '@/src/utils/generateClientPositionDocx';
import { getAnalysisForCategory } from '@/src/lib/api';
import useAnalysisQuery from '@/src/hooks/queries/useAnalysisQuery';
import { getIndustriesForNaceCode } from '@/src/lib/industries';

const ClientPosition = () => {

  const [marketPositionId] = useQueryState("id", { defaultValue: "" });
  const [isGenerating, setIsGenerating] = useState(false);

  const { data, isLoading, isError } = useClientPositionQuery(marketPositionId);

  // Market analysis for the client's industry (only industries with a generated analysis have one, e.g. cereals)
  const naceCode = data?.data?.market_position?.nace_code ?? "";
  const analysisCategory = getIndustriesForNaceCode(naceCode).find(industry => industry.analysisCategory)?.analysisCategory;
  const { data: marketAnalysisData } = useAnalysisQuery(analysisCategory ?? "", { enabled: !!analysisCategory });

  if (!marketPositionId) return <p>Potreban je identifikator tržišne pozicije</p>


  const clientPositionReport = data?.data;


  if (isLoading) return <AnalysisSkeleton />

  if (isError || !clientPositionReport) return <AnalysisError />

  const marketPosition = clientPositionReport.market_position;
  // When the LLM output can't be parsed the backend stores { error, raw_output } instead of the peer analysis
  const peerAnalysis = clientPositionReport.peer_analysis?.companies_analyzed ? clientPositionReport.peer_analysis : null

  const handleDownloadDocx = async () => {
    setIsGenerating(true);
    try {
      const marketAnalysis = marketAnalysisData?.data;

      await generateClientPositionDocx({
        ...clientPositionReport,
        peer_analysis: peerAnalysis,
        market_analysis: marketAnalysis,
      });
    } catch (error) {
      console.error('Error generating document:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button
          variant="contained"
          color='secondary'
          startIcon={<DownloadIcon />}
          onClick={handleDownloadDocx}
          disabled={isGenerating}

        >
          {isGenerating ? 'Generisanje...' : 'Preuzmi kao Word'}
        </Button>
      </div>

      <MarketPosition marketPosition={marketPosition} />

      <Divider />

      {peerAnalysis ?
        <PeerAnalysis peerAnalysis={peerAnalysis} /> :
        <p>Uporedna analiza se još generiše ili je došlo do greške</p>
      }

    </div>
  )
}

export default ClientPosition;
