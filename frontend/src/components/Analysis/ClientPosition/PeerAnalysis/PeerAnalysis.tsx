import { IPeerAnalysis } from "@/src/lib/api"
import cn from "@/src/utils/cn";
import capitalizeWords from "@/src/utils/helpers/capitalizeWords";
import KeyMetricsTable from "./KeyMetricsTable";
import { Divider } from "@mui/material";
import MarketStructureTable from "./MarketStructureTable";
import CompanyProfilesTable from "./CompanyProfilesTable";
import ReactMarkdown from 'react-markdown';
import KeyFindings from "./KeyFindings";
import PeerRankings from "./PeerRankings";


type PeerAnalysisProps = {
  peerAnalysis: IPeerAnalysis;
}

const PeerAnalysis = ({ peerAnalysis }: PeerAnalysisProps) => {

  return (
    <div className="flex flex-col gap-4">
      <div className='flex flex-col gap-1.5'>
        <h1 className="text-teal-100">
          {peerAnalysis.report_title}
        </h1>

        <h3 className="text-md">{peerAnalysis.sector}</h3>

        <p>
          <strong>Država: </strong>
          {peerAnalysis?.country}
        </p>
        <p>
          <strong>Period podataka: </strong>
          {peerAnalysis?.data_period}
        </p>

        <p>
          <strong>Valuta: </strong>
          {peerAnalysis?.currency}
        </p>

      </div>

      <div className="flex flex-col gap-2">

        <h5 className="mb-0 text-xs">Analizirana preduzeća:</h5>
        <ul className={cn(
          "flex flex-col w-[60%]",
          "[&>li]:flex [&>li]:justify-between [&>li]:border-b-1 [&>li]:border-steel-75 [&>li]:py-2 [&>li]:px-2 odd:[&>li]:bg-teal-10"
        )}>
          {peerAnalysis.companies_analyzed.map((company) => (
            <li key={company.short_name}>{capitalizeWords(company.name)} ({company.short_name})</li>
          ))}
        </ul>
      </div>

      {/* key metrics */}
      {Object.values(peerAnalysis.key_metrics_comparison).map((metric, index) => (
        <div className="flex flex-col gap-2" key={metric.metric_name_en}>
          <h5 className="mb-0 text-xs">Tržišni udeo ({metric.metric_name_en}):</h5>
          <KeyMetricsTable companies={metric.companies} />
          <p><strong>Ukupno za industriju: </strong>{metric.industry_total} RSD</p>

          {index !== 5 && <Divider />}
        </div>
      ))}

      <Divider />

      <MarketStructureTable metrics={peerAnalysis.key_metrics_comparison} />

      <CompanyProfilesTable companies={peerAnalysis.company_profiles} />

      <Divider />

      {/* peer rankings */}
      <PeerRankings peerRankings={peerAnalysis.peer_rankings} />

      <Divider />

      <div className="flex flex-col gap-3">
        <ReactMarkdown components={{
          h2: (props) => (
            <h2 className="font-bold text-teal-100" {...props} />
          ),
        }}>
          {peerAnalysis.analysis_narrative_md}
        </ReactMarkdown>
      </div>

      <Divider />

      <KeyFindings findings={peerAnalysis.key_findings} />

      <Divider />

      {/* limitations */}
      <div>
        <h4 className="font-semibold text-teal-100">Ograničenja:</h4>
        <ol className="list-disc mx-4 my-2">
          {peerAnalysis.limitations.map(limitation => <li key={limitation}>{limitation}</li>)}
        </ol>
      </div>

    </div>
  )
}

export default PeerAnalysis