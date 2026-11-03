'use client'
import Link from 'next/link';
import AnalysisError from '../Analysis.error';
import useMarketPositionsQuery from '@/src/hooks/queries/useMarketPositionsQuery';
import { CalendarToday, DescriptionOutlined, LabelImportantOutlined, Launch } from '@mui/icons-material';
import LatestMarketPositionSkeleton from './LatestMarketPositions.loading';
import { useQueryState } from 'nuqs';
import { getIndustriesForNaceCode } from '@/src/lib/industries';


const LatestMarketPositions = () => {

  const [clientName] = useQueryState("clientName", { defaultValue: "" })
  const [category] = useQueryState("category", { defaultValue: "" })

  const { data, isLoading, isError } = useMarketPositionsQuery({
    clientName: clientName,
    category: category
  });

  const res = data?.data;

  if (isLoading) return <LatestMarketPositionSkeleton />

  if (isError || !res) return <AnalysisError />

  const files = res.files

  const getMarketPositionFileId = (marketPosition: string) => (marketPosition?.split('/')[1]);

  return (
    <div className="flex flex-col gap-4 my-3">
      {getIndustriesForNaceCode(category).map(industry => (
        <Link key={industry.id} href={`/analysis/marketAnalysis?industry=${industry.id}`}
          className='flex gap-1 items-center'>
          Idi na tržišnu analizu: {industry.name}
          <Launch sx={{ fontSize: 17 }} />
        </Link>
      ))}
      {files.filter(file => file.content.analysis_id).map(analysis => (
        <div key={analysis.filename}>
          <Link className="px-6 py-4 flex flex-col justify-center w-full gap-3 border-1 rounded-xs border-charcoal-20 hover:border-yellow-70" href={`/analysis/client-position?id=${getMarketPositionFileId(analysis.content.analysis_id)}`}>
            <h4 className="font-md font-semibold"><DescriptionOutlined fontSize="small" color="disabled" /> {analysis.content.client_name}</h4>
            <div className="flex gap-4 align-center text-charcoal-80">
              <div className="text-xs flex items-center gap-4">
                <div className="flex items-center gap-1">
                  <CalendarToday sx={{ fontSize: 14 }} /> {new Date(analysis.last_modified).toLocaleDateString('sr-Latn-RS')} {new Date(analysis.last_modified).toLocaleTimeString('sr-Latn-RS')}
                </div>

                {analysis.content.nace_code &&
                  <div className="flex items-center gap-1">
                    <LabelImportantOutlined sx={{ fontSize: 18 }} /> {analysis.content.nace_code}
                  </div>
                }
              </div>
            </div>
          </Link>
        </div>
      ))}
      {files.length === 0 && <div className="text-center flex flex-col gap-3">
        <h3>Nema rezultata</h3>
        <p>Pokušajte sa drugim nazivom klijenta ili kategorijom</p>
      </div>}
    </div>
  )
}

export default LatestMarketPositions;
