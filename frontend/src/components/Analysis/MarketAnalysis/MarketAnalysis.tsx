'use client'
import ReactMarkdown from 'react-markdown';
import { Button, Divider } from '@mui/material';
import useAnalysisQuery from '@/src/hooks/queries/useAnalysisQuery';
import AnalysisError from '../Analysis.error';
import AnalysisSkeleton from '../Analysis.loading';
import BarChartDisplay from '../ChartDisplay/BarChartDisplay';
import LineChartDisplay from '../ChartDisplay/LineChartDisplay';
import MarketAnalysisTable from './MarketAnalysisTable';
import Link from 'next/link';
import { ReactNode, useState } from 'react';
import generateClientPositionDocx from '@/src/utils/generateClientPositionDocx';
import DownloadIcon from '@mui/icons-material/Download';

type MarketAnalysisProps = {
  category: string,
  title?: string,
  newAnalysisHref?: string,
  // Shown instead of the error when the category has no generated analysis yet
  fallback?: ReactNode
}

const MarketAnalysis = ({ category, title = category, newAnalysisHref = "/analysis/new", fallback }: MarketAnalysisProps) => {

  const { data, isLoading, isError } = useAnalysisQuery(category);
  const [isGenerating, setIsGenerating] = useState(false);

  const analysis = data?.data;

  if (isLoading) return <AnalysisSkeleton />

  if (isError || !analysis?.sections) return fallback ?? <AnalysisError />

  analysis.sections.forEach(section => {
    const match = section.content_md.match(/\{\{table:(\w+)\}\}/);
    section.tableId = match?.['1']
  })

  const handleDownloadDocx = async () => {
    setIsGenerating(true);
    try {

      await generateClientPositionDocx({
        market_analysis: analysis,
      });
    } catch (error) {
      console.error('Error generating document:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div>
      <div className='flex flex-col gap-1.5'>
        <div className="flex justify-between items-center">
          <p>
            Izabrana tržišna analiza:
          </p>
          <div className='flex flex-col gap-2'>

            <Link href={newAnalysisHref} prefetch={false}>
              Generiši novi UAF
            </Link>
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
        </div>
        <h1>
          {title}
        </h1>
        <h3 className="text-md">Izveštaj o analizi tržišta i cena</h3>

        <p>
          <strong>Datum generisanja: </strong>
          {new Date(analysis.generated_at).toLocaleDateString('sr-Latn-RS')}
        </p>

        <p>
          <strong>Period: </strong>
          {analysis.meta.period}
        </p>

        <p>
          <strong>Država: </strong>
          {analysis.meta.country}
        </p>

        <p>
          <strong>Sektor: </strong>
          {analysis.meta.sector}
        </p>
      </div>

      <Divider />

      {analysis?.sections?.map((section, index) =>
        <div key={section.id} className="flex flex-col gap-5">
          <h3>{section.title}</h3>
          <ReactMarkdown components={{
            h2: (props) => (
              <h2 className="font-bold text-teal-100" {...props} />
            ),
            p: (props) => {
              return props.children?.toString()?.match(/\{\{table:(\w+)\}\}/) ? <MarketAnalysisTable table={analysis.tables.find(t => t.id === section.tableId)} /> : <p {...props} />
            }
          }}>
            {section.content_md}
          </ReactMarkdown>

          {
            index !== analysis.sections.length - 1 &&
            <Divider />
          }
        </div>
      )}

      <Divider />

      {analysis.charts.map(chart => {
        const ChartComponent = chart.type === "bar" ? BarChartDisplay : LineChartDisplay;
        return <ChartComponent key={chart.id} data={chart.data} title={chart.title} />
      })}

      <Divider />

      <h4 className="font-semibold text-teal-100">Izvori:</h4>
      <ol className="list-disc mx-4 my-2 [&>li]:text-xs">
        {analysis.sources.map(source => <li key={source.name}>{source.name} {source.date}</li>)}
      </ol>
    </div>
  )
}

export default MarketAnalysis;