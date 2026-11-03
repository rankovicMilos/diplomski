'use client'
import { Divider } from '@mui/material';
import { IMarketPositionReport } from '@/src/lib/api';
import ReactMarkdown from 'react-markdown';
import MarketPositionAnalysis from './MarketPositionAnalysis';
import capitalizeWords from '@/src/utils/helpers/capitalizeWords';
import CommodityEstimateTable from './CommodityEstimateTable';
import MarketData from './MarketData';
import MarketAnalysisTable from '../../MarketAnalysis/MarketAnalysisTable';
import LineChartDisplay from '../../ChartDisplay/LineChartDisplay';
import PieChartDisplay from '../../ChartDisplay/PieChartDisplay'
import { BarChart } from '@mui/x-charts';

type MarketPositionProps = {
  marketPosition: IMarketPositionReport
}

const MarketPosition = ({ marketPosition }: MarketPositionProps) => {

  const clientFinancialsSummary = marketPosition.client_financials_summary;
  const commoditiesAnalyzes = marketPosition.commodities_analyzed

  const parsedWeightedMarketPositionCalculation = marketPosition.weighted_market_position.calculation_basis.replaceAll("_share", "")


  return (
    <div>
      <div className='flex flex-col gap-2'>
        <p>
          Analiza tržišne pozicije za:
        </p>
        <h1 className="text-teal-100">
          {marketPosition?.client_name}
        </h1>

        <h3 className="text-md">Izveštaj o analizi tržišta i cena</h3>

        <p>
          <strong>Naziv klijenta: </strong>
          {marketPosition?.client_name}
        </p>
        <p>
          <strong>Period analize: </strong>
          {marketPosition?.analysis_period}
        </p>

        <p>
          <strong>Valuta: </strong>
          {marketPosition?.currency}
        </p>

      </div>

      <Divider />

      <div className="flex flex-col gap-2">

        <ReactMarkdown components={{
          h2: (props) => (
            <h2 className="font-bold text-teal-100" {...props} />
          ),
          p: (props) => {
            const content = props.children?.toString() || '';

            // Check for table placeholder
            const tableMatch = content.match(/\{\{table:(\w+)\}\}/);
            if (tableMatch) {
              const tableId = tableMatch[1];
              const table = marketPosition.tables?.find(t => t.id === tableId);
              return <MarketAnalysisTable table={table} />;
            }

            // Check for chart placeholder
            const chartMatch = content.match(/\{\{chart:(\w+)\}\}/);
            if (chartMatch) {
              const chartId = chartMatch[1];
              const chart = marketPosition.charts?.find(c => c.id === chartId);
              if (chart) {
                if (chart.type === "bar") {
                  return (<div>
                    <h5 className="text-xs text-teal-100 font-semibold">{chart.title}:</h5>
                    <BarChart
                      xAxis={[{
                        scaleType: 'band', data: chart.data.map(d => d.label), categoryGapRatio: 0.4, barGapRatio: 0.15, colorMap: {
                          type: 'ordinal',
                          colors: ['#14b8a6', '#0ea5e9', '#8b5cf6', '#f59e0b']
                        }
                      }]}
                      yAxis={[{ label: chart?.y_axis_unit ?? "", min: 0 }]}
                      series={[{ data: chart.data.map(d => d.value) }]}
                      height={300}
                    />
                  </div>)
                }
                const ChartComponent = chart.type === 'pie' ? PieChartDisplay : LineChartDisplay;
                return <ChartComponent data={chart.data} title={chart.title} />;
              }
              return null;
            }

            return <p {...props} />;
          }
        }}>
          {marketPosition.analysis_narrative_md}
        </ReactMarkdown>
      </div>
      <Divider />

      {/* Comodities analyzed */}
      <div className="flex flex-col gap-3">
        {commoditiesAnalyzes.map((commodity) => (
          <div key={commodity.commodity} className="flex flex-col gap-1">
            <h3 className="text-teal-90 font-semibold">{capitalizeWords(commodity.commodity)}</h3>
            <p><strong>Udeo u prihodima: </strong>{commodity.revenue_share_pct}%</p>
            <p><strong>Procenjeni prihod: </strong>{commodity.estimated_revenue.value?.toLocaleString()} {commodity.estimated_revenue.unit}</p>
            <CommodityEstimateTable estimated_volume={commodity.estimated_volume} market_share={commodity.market_share} />
            <MarketData market_data={commodity.market_data} />
          </div>
        ))}
      </div>

      {/* weighted market position */}

      <div>
        <h4 className="font-semibold text-teal-100">Ponderisana tržišna pozicija</h4>
        <span className="text-xs">{marketPosition.weighted_market_position.methodology}</span>

        <div className='flex gap-3 my-4'>

          <div className="flex flex-col text-center rounded-md border py-5 w-[25%]" >
            <span className="text-xs">Niska procena</span>
            <span className="text-lg font-semibold">{marketPosition.weighted_market_position.weighted_market_share.low_estimate_pct}%</span>
          </div>

          <div className="flex flex-col text-center rounded-md border py-5 w-[25%]" >
            <span className="text-xs">Srednja procena</span>
            <span className="text-lg font-semibold">{marketPosition.weighted_market_position.weighted_market_share.mid_estimate_pct}%</span>
          </div>

          <div className="flex flex-col text-center rounded-md border py-5 w-[25%]" >
            <span className="text-xs">Visoka procena</span>
            <span className="text-lg font-semibold">{marketPosition.weighted_market_position.weighted_market_share.high_estimate_pct}%</span>
          </div>
        </div>

        <strong>Osnova proračuna:</strong>
        <p>{parsedWeightedMarketPositionCalculation}</p>
      </div>

      <Divider />
      <MarketPositionAnalysis methodology={marketPosition.market_position_analysis.methodology} assumptions={marketPosition.market_position_analysis.assumptions} />

      {/* Client financials summary */}
      <div className='flex flex-col gap-1.5'>

        <h4 className="font-semibold text-teal-100">Pregled finansija klijenta:</h4>
        <p>
          <strong>Ukupan prihod za godinu {clientFinancialsSummary.total_revenue.year}: </strong>
          {clientFinancialsSummary.total_revenue.value?.toLocaleString()}{" "}
          {clientFinancialsSummary.total_revenue.unit}
        </p>
        <p>{clientFinancialsSummary.revenue_trend}</p>
      </div>

      <Divider />

      {/* Limitations and caveats */}
      <h4 className="font-semibold text-teal-100">Ograničenja i napomene:</h4>
      <ol className="list-disc mx-4 my-2">
        {marketPosition.limitations_and_caveats.map(limitation => <li key={limitation}>{limitation}</li>)}
      </ol>

      <Divider />

      <h4 className="font-semibold text-teal-100">Izvori:</h4>
      <ol className="list-disc mx-4 my-2 [&>li]:text-xs">
        {marketPosition.sources.map(source => <li key={source.name}>{`${source.name} (${source.type.replaceAll("_", " ")})`}</li>)}
      </ol>
    </div >
  )
}

export default MarketPosition;
