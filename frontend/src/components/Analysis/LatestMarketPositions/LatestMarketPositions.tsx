'use client'
import Link from 'next/link';
import AnalysisError from '../Analysis.error';
import useMarketPositionsQuery from '@/src/hooks/queries/useMarketPositionsQuery';
import { ArrowForward, CalendarToday, DescriptionOutlined, LabelImportantOutlined, Launch } from '@mui/icons-material';
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
          className='inline-flex w-fit gap-2 items-center glass glass-hover rounded-full px-4 py-2 text-xs font-semibold text-teal-100 transition-colors duration-200 hover:bg-teal-20'>
          Idi na tržišnu analizu: {industry.name}
          <Launch sx={{ fontSize: 17 }} />
        </Link>
      ))}
      {files.filter(file => file.content.analysis_id).map(analysis => (
        <div key={analysis.filename}>
          <Link className="glass glass-hover group relative px-6 py-5 flex flex-col justify-center w-full gap-3 rounded-md" href={`/analysis/client-position?id=${getMarketPositionFileId(analysis.content.analysis_id)}`}>
            <h4 className="font-md font-semibold flex items-center gap-3 pr-10"><span className="flex h-9 w-9 items-center justify-center rounded-xs bg-teal-10 text-teal-100"><DescriptionOutlined fontSize="small" /></span> {analysis.content.client_name}</h4>
            <ArrowForward aria-hidden className="absolute right-6 top-1/2 -translate-y-1/2 text-charcoal-40 transition-colors duration-200 group-hover:text-teal-100" fontSize="small" />
            <div className="flex gap-4 align-center text-charcoal-80">
              <div className="text-xs flex items-center gap-4">
                <div className="flex items-center gap-1 rounded-full bg-steel-30 px-3 py-1">
                  <CalendarToday sx={{ fontSize: 14 }} /> {new Date(analysis.last_modified).toLocaleDateString('sr-Latn-RS')} {new Date(analysis.last_modified).toLocaleTimeString('sr-Latn-RS')}
                </div>

                {analysis.content.nace_code &&
                  <div className="flex items-center gap-1 rounded-full bg-teal-10 px-3 py-1 text-teal-100 font-semibold">
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
